"""
SSO Session Manager
===================
Single Sign-On session tracking, revocation, and concurrent session control.
Manages IdP-initiated and SP-initiated SSO flows.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class SSOProvider(str, Enum):
    SAML2 = "saml2"
    OIDC = "oidc"
    OAUTH2 = "oauth2"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"


class SessionState(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_MFA = "pending_mfa"


@dataclass
class SSOSession:
    session_id: str
    user_id: str
    tenant_id: str
    provider: SSOProvider
    provider_session_id: str   # IdP-side session identifier
    ip_address: str
    user_agent: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    state: SessionState = SessionState.ACTIVE
    mfa_verified: bool = False
    scopes: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    idle_timeout: int = 1800        # 30 minutes
    absolute_timeout: int = 28800   # 8 hours

    @property
    def is_expired(self) -> bool:
        now = time.time()
        if now > self.created_at + self.absolute_timeout:
            return True
        if now > self.last_activity + self.idle_timeout:
            return True
        return False

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_activity

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
        if self.state == SessionState.IDLE:
            self.state = SessionState.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "provider": self.provider.value,
            "provider_session_id": self.provider_session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent[:80],
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "state": self.state.value,
            "mfa_verified": self.mfa_verified,
            "scopes": list(self.scopes),
            "age_seconds": round(self.age_seconds, 1),
            "idle_seconds": round(self.idle_seconds, 1),
            "is_expired": self.is_expired,
        }


@dataclass
class RevocationRecord:
    session_id: str
    user_id: str
    reason: str
    revoked_at: float = field(default_factory=time.time)
    revoked_by: str = "system"


class SSOSessionManager:
    """
    Manages SSO sessions across multiple IdP providers.
    Supports idle/absolute timeouts, MFA step-up, and bulk revocation.
    """

    def __init__(
        self,
        max_sessions_per_user: int = 5,
        default_idle_timeout: int = 1800,
        default_absolute_timeout: int = 28800,
    ) -> None:
        self._sessions: Dict[str, SSOSession] = {}
        self._user_sessions: Dict[str, Set[str]] = {}   # user_id -> session_ids
        self._revocation_log: List[RevocationRecord] = []
        self.max_sessions_per_user = max_sessions_per_user
        self.default_idle_timeout = default_idle_timeout
        self.default_absolute_timeout = default_absolute_timeout

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        provider: SSOProvider,
        provider_session_id: str,
        ip_address: str,
        user_agent: str,
        scopes: Optional[Set[str]] = None,
        require_mfa: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SSOSession:
        """Create a new SSO session, evicting oldest if over limit."""
        self._evict_expired_for_user(user_id)
        user_sessions = self._user_sessions.get(user_id, set())

        if len(user_sessions) >= self.max_sessions_per_user:
            self._evict_oldest_session(user_id)

        session_id = secrets.token_urlsafe(32)
        session = SSOSession(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            provider=provider,
            provider_session_id=provider_session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes=scopes or set(),
            state=SessionState.PENDING_MFA if require_mfa else SessionState.ACTIVE,
            mfa_verified=not require_mfa,
            idle_timeout=self.default_idle_timeout,
            absolute_timeout=self.default_absolute_timeout,
            metadata=metadata or {},
        )
        self._sessions[session_id] = session
        self._user_sessions.setdefault(user_id, set()).add(session_id)
        return session

    def get_session(self, session_id: str) -> Optional[SSOSession]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired:
            self._expire_session(session)
            return None
        return session

    def touch_session(self, session_id: str) -> bool:
        """Refresh session activity timestamp. Returns False if session not found/expired."""
        session = self.get_session(session_id)
        if session is None:
            return False
        session.touch()
        return True

    def complete_mfa(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session and session.state == SessionState.PENDING_MFA:
            session.mfa_verified = True
            session.state = SessionState.ACTIVE
            return True
        return False

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------

    def revoke_session(
        self, session_id: str, reason: str = "user_logout", revoked_by: str = "system"
    ) -> bool:
        session = self._sessions.pop(session_id, None)
        if not session:
            return False
        session.state = SessionState.REVOKED
        user_sessions = self._user_sessions.get(session.user_id, set())
        user_sessions.discard(session_id)
        self._revocation_log.append(
            RevocationRecord(
                session_id=session_id,
                user_id=session.user_id,
                reason=reason,
                revoked_by=revoked_by,
            )
        )
        return True

    def revoke_all_user_sessions(
        self, user_id: str, reason: str = "admin_revocation", revoked_by: str = "admin"
    ) -> int:
        session_ids = list(self._user_sessions.get(user_id, set()))
        count = 0
        for sid in session_ids:
            if self.revoke_session(sid, reason=reason, revoked_by=revoked_by):
                count += 1
        self._user_sessions.pop(user_id, None)
        return count

    def revoke_by_provider_session(
        self, provider_session_id: str, reason: str = "idp_logout"
    ) -> int:
        """Revoke local sessions that share a given IdP session ID (SLO support)."""
        to_revoke = [
            sid for sid, s in self._sessions.items()
            if s.provider_session_id == provider_session_id
        ]
        for sid in to_revoke:
            self.revoke_session(sid, reason=reason)
        return len(to_revoke)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_user_sessions(self, user_id: str) -> List[SSOSession]:
        session_ids = self._user_sessions.get(user_id, set())
        sessions = []
        for sid in list(session_ids):
            session = self.get_session(sid)
            if session:
                sessions.append(session)
        return sessions

    def count_active_sessions(self) -> int:
        return sum(
            1 for s in self._sessions.values()
            if s.state == SessionState.ACTIVE and not s.is_expired
        )

    def count_user_sessions(self, user_id: str) -> int:
        return len(self.get_user_sessions(user_id))

    def is_session_valid(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        return session is not None and session.state == SessionState.ACTIVE and session.mfa_verified

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def purge_expired_sessions(self) -> int:
        expired = [
            sid for sid, s in self._sessions.items() if s.is_expired
        ]
        for sid in expired:
            self._expire_session(self._sessions[sid])
        return len(expired)

    def _expire_session(self, session: SSOSession) -> None:
        session.state = SessionState.EXPIRED
        self._sessions.pop(session.session_id, None)
        user_sessions = self._user_sessions.get(session.user_id, set())
        user_sessions.discard(session.session_id)

    def _evict_expired_for_user(self, user_id: str) -> None:
        session_ids = list(self._user_sessions.get(user_id, set()))
        for sid in session_ids:
            s = self._sessions.get(sid)
            if s and s.is_expired:
                self._expire_session(s)

    def _evict_oldest_session(self, user_id: str) -> None:
        session_ids = self._user_sessions.get(user_id, set())
        sessions = [self._sessions[sid] for sid in session_ids if sid in self._sessions]
        if sessions:
            oldest = min(sessions, key=lambda s: s.created_at)
            self.revoke_session(oldest.session_id, reason="session_limit_eviction")

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def get_revocation_log(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        log = self._revocation_log
        if user_id:
            log = [r for r in log if r.user_id == user_id]
        return [
            {
                "session_id": r.session_id,
                "user_id": r.user_id,
                "reason": r.reason,
                "revoked_at": r.revoked_at,
                "revoked_by": r.revoked_by,
            }
            for r in log
        ]

    def stats(self) -> Dict[str, Any]:
        all_sessions = list(self._sessions.values())
        return {
            "total_sessions": len(all_sessions),
            "active": sum(1 for s in all_sessions if s.state == SessionState.ACTIVE),
            "pending_mfa": sum(1 for s in all_sessions if s.state == SessionState.PENDING_MFA),
            "revocation_log_size": len(self._revocation_log),
            "unique_users": len(self._user_sessions),
        }
