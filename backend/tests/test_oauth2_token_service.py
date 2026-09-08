"""Tests for OAuth2PKCETokenService."""

import unittest
from backend.services.enterprise.oauth2_token_service import (
    OAuth2PKCETokenService,
    GrantType,
    CodeChallengeMethod,
    TokenType,
)


class TestOAuth2PKCETokenService(unittest.TestCase):

    def setUp(self):
        self.service = OAuth2PKCETokenService(
            access_token_ttl=3600,
            refresh_token_ttl=86400,
            auth_code_ttl=600,
        )
        self.service.register_client(
            client_id="client_web",
            client_secret="secret_abc",
            redirect_uris=["https://app.elviq.io/callback"],
            scopes={"openid", "profile", "meetings:read", "meetings:write"},
            name="Web Client",
        )

    def test_register_client(self):
        client = self.service.get_client("client_web")
        self.assertIsNotNone(client)
        self.assertEqual(client.client_id, "client_web")

    def test_authenticate_client_valid(self):
        self.assertTrue(self.service.authenticate_client("client_web", "secret_abc"))

    def test_authenticate_client_invalid(self):
        self.assertFalse(self.service.authenticate_client("client_web", "wrong"))

    def test_generate_code_verifier(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        self.assertIsInstance(verifier, str)
        self.assertGreater(len(verifier), 40)

    def test_generate_code_challenge_s256(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(
            verifier, CodeChallengeMethod.S256
        )
        self.assertIsInstance(challenge, str)
        self.assertGreater(len(challenge), 40)

    def test_verify_code_challenge_valid(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)
        self.assertTrue(
            OAuth2PKCETokenService.verify_code_challenge(verifier, challenge, CodeChallengeMethod.S256)
        )

    def test_verify_code_challenge_invalid(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)
        self.assertFalse(
            OAuth2PKCETokenService.verify_code_challenge("wrong_verifier", challenge, CodeChallengeMethod.S256)
        )

    def test_full_pkce_flow(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)

        auth_code = self.service.create_authorization_code(
            client_id="client_web",
            user_id="user_123",
            redirect_uri="https://app.elviq.io/callback",
            scopes={"openid", "profile"},
            code_challenge=challenge,
        )
        self.assertIsNotNone(auth_code.code)
        self.assertFalse(auth_code.is_expired)

        token = self.service.exchange_code_for_token(
            code=auth_code.code,
            client_id="client_web",
            redirect_uri="https://app.elviq.io/callback",
            code_verifier=verifier,
        )
        self.assertIsNotNone(token.token)
        self.assertEqual(token.user_id, "user_123")
        self.assertFalse(token.is_expired)

    def test_exchange_code_twice_fails(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)
        auth_code = self.service.create_authorization_code(
            "client_web", "user_789", "https://app.elviq.io/callback",
            {"openid"}, challenge,
        )
        self.service.exchange_code_for_token(
            auth_code.code, "client_web", "https://app.elviq.io/callback", verifier
        )
        with self.assertRaises(ValueError):
            self.service.exchange_code_for_token(
                auth_code.code, "client_web", "https://app.elviq.io/callback", verifier
            )

    def test_refresh_token(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)
        auth_code = self.service.create_authorization_code(
            "client_web", "user_456", "https://app.elviq.io/callback",
            {"openid"}, challenge,
        )
        token = self.service.exchange_code_for_token(
            auth_code.code, "client_web", "https://app.elviq.io/callback", verifier
        )
        new_token = self.service.refresh_access_token(token.refresh_token, "client_web")
        self.assertIsNotNone(new_token.token)
        self.assertNotEqual(new_token.token, token.token)

    def test_token_introspection_active(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)
        auth_code = self.service.create_authorization_code(
            "client_web", "user_111", "https://app.elviq.io/callback",
            {"openid"}, challenge,
        )
        token = self.service.exchange_code_for_token(
            auth_code.code, "client_web", "https://app.elviq.io/callback", verifier
        )
        result = self.service.introspect_token(token.token)
        self.assertTrue(result.active)
        self.assertEqual(result.user_id, "user_111")

    def test_token_introspection_invalid(self):
        result = self.service.introspect_token("invalid_token_xyz")
        self.assertFalse(result.active)

    def test_revoke_token(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier, CodeChallengeMethod.S256)
        auth_code = self.service.create_authorization_code(
            "client_web", "user_222", "https://app.elviq.io/callback",
            {"openid"}, challenge,
        )
        token = self.service.exchange_code_for_token(
            auth_code.code, "client_web", "https://app.elviq.io/callback", verifier
        )
        revoked = self.service.revoke_token(token.token)
        self.assertTrue(revoked)
        result = self.service.introspect_token(token.token)
        self.assertFalse(result.active)

    def test_build_authorization_url(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier)
        url = OAuth2PKCETokenService.build_authorization_url(
            base_url="https://auth.elviq.io/authorize",
            client_id="client_web",
            redirect_uri="https://app.elviq.io/callback",
            scopes=["openid", "profile"],
            state="random_state_123",
            code_challenge=challenge,
        )
        self.assertIn("response_type=code", url)
        self.assertIn("code_challenge=", url)
        self.assertIn("state=", url)

    def test_stats(self):
        s = self.service.stats()
        self.assertIn("registered_clients", s)
        self.assertGreaterEqual(s["registered_clients"], 1)

    def test_token_response_format(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier)
        auth_code = self.service.create_authorization_code(
            "client_web", "user_333", "https://app.elviq.io/callback",
            {"openid"}, challenge,
        )
        token = self.service.exchange_code_for_token(
            auth_code.code, "client_web", "https://app.elviq.io/callback", verifier
        )
        resp = token.to_response()
        self.assertIn("access_token", resp)
        self.assertIn("token_type", resp)
        self.assertIn("expires_in", resp)

    def test_invalid_redirect_uri(self):
        verifier = OAuth2PKCETokenService.generate_code_verifier()
        challenge = OAuth2PKCETokenService.generate_code_challenge(verifier)
        with self.assertRaises(ValueError):
            self.service.create_authorization_code(
                "client_web", "user_444", "https://evil.site/callback",
                {"openid"}, challenge,
            )


if __name__ == "__main__":
    unittest.main()
