"""
OAuth2 Token Service
====================
OAuth 2.0 PKCE (Proof Key for Code Exchange) flow implementation.
Handles authorization code exchange, token introspection, and refresh.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlencode


class GrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"


class TokenType(str, Enum):
    BEARER = "Bearer"
    MAC = "MAC"
    DPOP = "DPoP"


class CodeChallengeMethod(str, Enum):
    S256 = "S256"
    PLAIN = "plain"


@dataclass
class OAuthClient:
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    scopes: Set[str]
    grant_types: List[GrantType]
    is_confidential: bool = True
    name: str = ""
    description: str = ""


@dataclass
class AuthorizationCode:
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: Set[str]
    code_challenge: str
    code_challenge_method: CodeChallengeMethod
    issued_at: float = field(default_factory=time.time)
    expires_in: int = 600  # 10 minutes

    @property
    def is_expired(self) -> bool:
        return time.time() > self.issued_at + self.expires_in


@dataclass
class AccessToken:
    token: str
    token_type: TokenType
    client_id: str
    user_id: str
    scopes: Set[str]
    issued_at: float = field(default_factory=time.time)
    expires_in: int = 3600  # 1 hour
    refresh_token: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return time.time() > self.issued_at + self.expires_in

    def to_response(self) -> Dict[str, Any]:
        resp: Dict[str, Any] = {
            "access_token": self.token,
            "token_type": self.token_type.value,
            "expires_in": self.expires_in,
            "scope": " ".join(sorted(self.scopes)),
        }
        if self.refresh_token:
            resp["refresh_token"] = self.refresh_token
        return resp


@dataclass
class TokenIntrospectionResult:
    active: bool
    token: str
    client_id: str = ""
    user_id: str = ""
    scopes: Set[str] = field(default_factory=set)
    exp: int = 0
    iat: int = 0
    token_type: str = TokenType.BEARER.value

    def to_dict(self) -> Dict[str, Any]:
        if not self.active:
            return {"active": False}
        return {
            "active": True,
            "client_id": self.client_id,
            "sub": self.user_id,
            "scope": " ".join(sorted(self.scopes)),
            "exp": self.exp,
            "iat": self.iat,
            "token_type": self.token_type,
        }


class OAuth2PKCETokenService:
    """
    Full OAuth 2.0 authorization server with PKCE support.
    Manages clients, auth codes, access tokens, and refresh tokens.
    """

    def __init__(
        self,
        access_token_ttl: int = 3600,
        refresh_token_ttl: int = 86400 * 30,
        auth_code_ttl: int = 600,
    ) -> None:
        self._clients: Dict[str, OAuthClient] = {}
        self._auth_codes: Dict[str, AuthorizationCode] = {}
        self._access_tokens: Dict[str, AccessToken] = {}
        self._refresh_tokens: Dict[str, AccessToken] = {}
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl
        self.auth_code_ttl = auth_code_ttl

    # ------------------------------------------------------------------
    # Client registration
    # ------------------------------------------------------------------

    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        scopes: Set[str],
        grant_types: Optional[List[GrantType]] = None,
        name: str = "",
    ) -> OAuthClient:
        client = OAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=redirect_uris,
            scopes=scopes,
            grant_types=grant_types or [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
            name=name,
        )
        self._clients[client_id] = client
        return client

    def get_client(self, client_id: str) -> Optional[OAuthClient]:
        return self._clients.get(client_id)

    def authenticate_client(self, client_id: str, client_secret: str) -> bool:
        client = self._clients.get(client_id)
        if not client:
            return False
        return hmac.compare_digest(client.client_secret, client_secret)

    # ------------------------------------------------------------------
    # PKCE helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_code_verifier(length: int = 64) -> str:
        """Generate RFC 7636 compliant code verifier."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_code_challenge(
        verifier: str, method: CodeChallengeMethod = CodeChallengeMethod.S256
    ) -> str:
        """Derive code challenge from verifier."""
        if method == CodeChallengeMethod.S256:
            digest = hashlib.sha256(verifier.encode()).digest()
            return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return verifier  # plain

    @staticmethod
    def verify_code_challenge(
        verifier: str, challenge: str, method: CodeChallengeMethod
    ) -> bool:
        """Verify the PKCE code challenge against the verifier."""
        expected = OAuth2PKCETokenService.generate_code_challenge(verifier, method)
        return hmac.compare_digest(expected, challenge)

    # ------------------------------------------------------------------
    # Authorization code flow
    # ------------------------------------------------------------------

    def create_authorization_code(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scopes: Set[str],
        code_challenge: str,
        code_challenge_method: CodeChallengeMethod = CodeChallengeMethod.S256,
    ) -> AuthorizationCode:
        client = self._clients.get(client_id)
        if not client:
            raise ValueError(f"Unknown client_id: {client_id}")
        if redirect_uri not in client.redirect_uris:
            raise ValueError("Invalid redirect_uri")
        if not scopes.issubset(client.scopes):
            raise ValueError("Requested scopes exceed client capabilities")

        code_str = secrets.token_urlsafe(32)
        auth_code = AuthorizationCode(
            code=code_str,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            expires_in=self.auth_code_ttl,
        )
        self._auth_codes[code_str] = auth_code
        return auth_code

    def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> AccessToken:
        auth_code = self._auth_codes.pop(code, None)
        if not auth_code:
            raise ValueError("Invalid or already-used authorization code")
        if auth_code.is_expired:
            raise ValueError("Authorization code expired")
        if auth_code.client_id != client_id:
            raise ValueError("client_id mismatch")
        if auth_code.redirect_uri != redirect_uri:
            raise ValueError("redirect_uri mismatch")
        if not self.verify_code_challenge(
            code_verifier, auth_code.code_challenge, auth_code.code_challenge_method
        ):
            raise ValueError("PKCE code_verifier mismatch")

        return self._issue_token(client_id, auth_code.user_id, auth_code.scopes)

    # ------------------------------------------------------------------
    # Token issuance
    # ------------------------------------------------------------------

    def _issue_token(
        self, client_id: str, user_id: str, scopes: Set[str]
    ) -> AccessToken:
        access_token_str = secrets.token_urlsafe(48)
        refresh_token_str = secrets.token_urlsafe(48)

        token = AccessToken(
            token=access_token_str,
            token_type=TokenType.BEARER,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_in=self.access_token_ttl,
            refresh_token=refresh_token_str,
        )
        self._access_tokens[access_token_str] = token
        self._refresh_tokens[refresh_token_str] = token
        return token

    def refresh_access_token(
        self, refresh_token: str, client_id: str
    ) -> AccessToken:
        old_token = self._refresh_tokens.pop(refresh_token, None)
        if not old_token:
            raise ValueError("Invalid refresh_token")
        if old_token.client_id != client_id:
            raise ValueError("client_id mismatch")
        # Revoke old access token
        self._access_tokens.pop(old_token.token, None)
        return self._issue_token(client_id, old_token.user_id, old_token.scopes)

    # ------------------------------------------------------------------
    # Token introspection (RFC 7662)
    # ------------------------------------------------------------------

    def introspect_token(self, token: str) -> TokenIntrospectionResult:
        access_token = self._access_tokens.get(token)
        if not access_token or access_token.is_expired:
            return TokenIntrospectionResult(active=False, token=token)
        return TokenIntrospectionResult(
            active=True,
            token=token,
            client_id=access_token.client_id,
            user_id=access_token.user_id,
            scopes=access_token.scopes,
            exp=int(access_token.issued_at + access_token.expires_in),
            iat=int(access_token.issued_at),
            token_type=access_token.token_type.value,
        )

    # ------------------------------------------------------------------
    # Token revocation (RFC 7009)
    # ------------------------------------------------------------------

    def revoke_token(self, token: str) -> bool:
        if token in self._access_tokens:
            at = self._access_tokens.pop(token)
            if at.refresh_token:
                self._refresh_tokens.pop(at.refresh_token, None)
            return True
        if token in self._refresh_tokens:
            rt_at = self._refresh_tokens.pop(token)
            self._access_tokens.pop(rt_at.token, None)
            return True
        return False

    # ------------------------------------------------------------------
    # Authorization URL helper
    # ------------------------------------------------------------------

    @staticmethod
    def build_authorization_url(
        base_url: str,
        client_id: str,
        redirect_uri: str,
        scopes: List[str],
        state: str,
        code_challenge: str,
        code_challenge_method: CodeChallengeMethod = CodeChallengeMethod.S256,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method.value,
        }
        return f"{base_url}?{urlencode(params)}"

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, int]:
        return {
            "registered_clients": len(self._clients),
            "pending_auth_codes": len(self._auth_codes),
            "active_access_tokens": sum(
                1 for t in self._access_tokens.values() if not t.is_expired
            ),
            "active_refresh_tokens": len(self._refresh_tokens),
        }
