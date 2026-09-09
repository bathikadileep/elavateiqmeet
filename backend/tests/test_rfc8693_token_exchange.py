"""
Tests for Enterprise Zero-Trust Token Exchange & Security Token Service (STS)
=============================================================================
Validates RFC 8693 OAuth 2.0 token exchange grant type, actor delegation,
scope restriction, and signature verification.
"""

import unittest
from backend.services.enterprise.rfc8693_token_exchange import (
    SecurityTokenService,
    TokenExchangeRequest,
    TOKEN_EXCHANGE_GRANT_TYPE,
    ACCESS_TOKEN_TYPE,
)


class TestRfc8693TokenExchange(unittest.TestCase):

    def setUp(self):
        self.sts = SecurityTokenService()
        self.host_sub = "usr_host_alice"
        self.ai_coach_sub = "svc_ai_coach_agent"

        # Pre-mint valid tokens
        self.host_token = self.sts.create_mock_subject_token(
            sub=self.host_sub,
            scopes=["meeting:read", "meeting:write", "meeting:record", "transcription:read"],
        )
        self.coach_token = self.sts.create_mock_subject_token(
            sub=self.ai_coach_sub,
            scopes=["ai:coach", "transcription:read"],
        )

    def test_direct_subject_token_exchange(self):
        req = TokenExchangeRequest(
            grant_type=TOKEN_EXCHANGE_GRANT_TYPE,
            subject_token=self.host_token,
            subject_token_type=ACCESS_TOKEN_TYPE,
            audience="elevateiq-recording-service",
            scope="meeting:read meeting:record",
        )

        success, token, err = self.sts.exchange_token(req, client_id="web-app-v2")
        self.assertTrue(success)
        self.assertIsNone(err)
        self.assertIsNotNone(token)
        self.assertEqual(token.subject, self.host_sub)
        self.assertIsNone(token.actor)
        self.assertEqual(token.scope, "meeting:read meeting:record")

    def test_delegated_token_exchange_with_actor(self):
        # AI Coach requests delegation token to access transcription on behalf of host
        req = TokenExchangeRequest(
            grant_type=TOKEN_EXCHANGE_GRANT_TYPE,
            subject_token=self.host_token,
            subject_token_type=ACCESS_TOKEN_TYPE,
            actor_token=self.coach_token,
            actor_token_type=ACCESS_TOKEN_TYPE,
            audience="elevateiq-ai-pipeline",
            scope="transcription:read",
        )

        success, token, err = self.sts.exchange_token(req, client_id="ai-coach-daemon")
        self.assertTrue(success)
        self.assertIsNotNone(token)
        self.assertEqual(token.subject, self.host_sub)
        self.assertEqual(token.actor, self.ai_coach_sub)
        self.assertEqual(token.scope, "transcription:read")

    def test_scope_elevation_rejected(self):
        # Host only has meeting:read, tries to request video:stream
        limited_token = self.sts.create_mock_subject_token(
            sub="usr_guest",
            scopes=["meeting:read"],
        )

        req = TokenExchangeRequest(
            grant_type=TOKEN_EXCHANGE_GRANT_TYPE,
            subject_token=limited_token,
            subject_token_type=ACCESS_TOKEN_TYPE,
            scope="meeting:read video:stream",
        )

        success, token, err = self.sts.exchange_token(req, client_id="guest-client")
        self.assertFalse(success)
        self.assertIn("Cannot elevate scope", err)

    def test_invalid_grant_type_rejected(self):
        req = TokenExchangeRequest(
            grant_type="authorization_code",
            subject_token=self.host_token,
            subject_token_type=ACCESS_TOKEN_TYPE,
        )

        success, token, err = self.sts.exchange_token(req, client_id="web-app")
        self.assertFalse(success)
        self.assertIn("Unsupported grant_type", err)


if __name__ == "__main__":
    unittest.main()
