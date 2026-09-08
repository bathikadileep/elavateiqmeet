"""Tests for SSOSessionManager."""

import unittest
from backend.services.enterprise.sso_session_manager import (
    SSOSessionManager,
    SSOProvider,
    SessionState,
)


class TestSSOSessionManager(unittest.TestCase):

    def setUp(self):
        self.manager = SSOSessionManager(
            max_sessions_per_user=3,
            default_idle_timeout=1800,
            default_absolute_timeout=28800,
        )

    def _create_session(self, user_id="user_001", provider_session_id="idp_sess_1"):
        return self.manager.create_session(
            user_id=user_id,
            tenant_id="tenant_acme",
            provider=SSOProvider.SAML2,
            provider_session_id=provider_session_id,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
            scopes={"openid", "profile"},
        )

    def test_create_session(self):
        session = self._create_session()
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.user_id, "user_001")
        self.assertEqual(session.state, SessionState.ACTIVE)

    def test_create_session_with_mfa(self):
        session = self.manager.create_session(
            user_id="user_mfa",
            tenant_id="tenant_acme",
            provider=SSOProvider.OIDC,
            provider_session_id="oidc_sess_1",
            ip_address="10.0.0.1",
            user_agent="Chrome",
            require_mfa=True,
        )
        self.assertEqual(session.state, SessionState.PENDING_MFA)
        self.assertFalse(session.mfa_verified)

    def test_complete_mfa(self):
        session = self.manager.create_session(
            "user_mfa2", "t1", SSOProvider.OIDC, "oidc_2", "10.0.0.1", "Chrome",
            require_mfa=True,
        )
        success = self.manager.complete_mfa(session.session_id)
        self.assertTrue(success)
        updated = self.manager.get_session(session.session_id)
        self.assertTrue(updated.mfa_verified)
        self.assertEqual(updated.state, SessionState.ACTIVE)

    def test_get_session_valid(self):
        session = self._create_session("user_002")
        retrieved = self.manager.get_session(session.session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.session_id, session.session_id)

    def test_get_session_nonexistent(self):
        result = self.manager.get_session("nonexistent_session_id")
        self.assertIsNone(result)

    def test_touch_session(self):
        session = self._create_session("user_003")
        result = self.manager.touch_session(session.session_id)
        self.assertTrue(result)

    def test_revoke_session(self):
        session = self._create_session("user_004")
        revoked = self.manager.revoke_session(session.session_id, reason="logout")
        self.assertTrue(revoked)
        self.assertIsNone(self.manager.get_session(session.session_id))

    def test_revoke_nonexistent_session(self):
        result = self.manager.revoke_session("fake_session", reason="test")
        self.assertFalse(result)

    def test_revoke_all_user_sessions(self):
        s1 = self._create_session("user_005", "idp_s1")
        s2 = self._create_session("user_005", "idp_s2")
        count = self.manager.revoke_all_user_sessions("user_005")
        self.assertGreaterEqual(count, 2)
        self.assertIsNone(self.manager.get_session(s1.session_id))
        self.assertIsNone(self.manager.get_session(s2.session_id))

    def test_revoke_by_provider_session(self):
        s = self._create_session("user_006", "shared_idp_sess")
        count = self.manager.revoke_by_provider_session("shared_idp_sess")
        self.assertGreaterEqual(count, 1)
        self.assertIsNone(self.manager.get_session(s.session_id))

    def test_get_user_sessions(self):
        self._create_session("user_007", "s1")
        self._create_session("user_007", "s2")
        sessions = self.manager.get_user_sessions("user_007")
        self.assertEqual(len(sessions), 2)

    def test_max_sessions_per_user_eviction(self):
        for i in range(5):
            self._create_session("user_008", f"idp_s{i}")
        sessions = self.manager.get_user_sessions("user_008")
        self.assertLessEqual(len(sessions), self.manager.max_sessions_per_user)

    def test_is_session_valid_active(self):
        session = self._create_session("user_009")
        self.assertTrue(self.manager.is_session_valid(session.session_id))

    def test_is_session_valid_pending_mfa(self):
        session = self.manager.create_session(
            "user_010", "t1", SSOProvider.SAML2, "idp_mfa", "10.0.0.1", "Chrome",
            require_mfa=True,
        )
        self.assertFalse(self.manager.is_session_valid(session.session_id))

    def test_count_active_sessions(self):
        initial = self.manager.count_active_sessions()
        self._create_session("user_011")
        self.assertEqual(self.manager.count_active_sessions(), initial + 1)

    def test_purge_expired_sessions(self):
        # Manually age out a session
        session = self._create_session("user_012")
        self.manager._sessions[session.session_id].absolute_timeout = -1
        purged = self.manager.purge_expired_sessions()
        self.assertGreaterEqual(purged, 1)

    def test_revocation_log_populated(self):
        session = self._create_session("user_013")
        self.manager.revoke_session(session.session_id, reason="test_reason")
        log = self.manager.get_revocation_log(user_id="user_013")
        self.assertGreater(len(log), 0)
        self.assertEqual(log[-1]["reason"], "test_reason")

    def test_session_to_dict(self):
        session = self._create_session("user_014")
        d = session.to_dict()
        self.assertIn("session_id", d)
        self.assertIn("user_id", d)
        self.assertIn("state", d)
        self.assertIn("is_expired", d)

    def test_stats(self):
        self._create_session("user_015")
        stats = self.manager.stats()
        self.assertIn("total_sessions", stats)
        self.assertGreaterEqual(stats["total_sessions"], 1)


if __name__ == "__main__":
    unittest.main()
