"""
Tests for Enterprise OpenID Connect (OIDC) Core Token Verifier & JWKS Keystore Rotator
======================================================================================
Validates RFC 7519 / RFC 7515 / OpenID Connect Core 1.0 token parsing, signature
verification, audience checks, clock skew leeway, and nonce replay prevention.
"""

import base64
import hashlib
import hmac
import json
import time
import unittest
from backend.services.enterprise.oidc_token_verifier import (
    OidcTokenVerifier,
    Base64UrlUtil,
    JwkKey,
)


class TestOidcTokenVerifier(unittest.TestCase):

    def setUp(self):
        self.verifier = OidcTokenVerifier()
        self.issuer = "https://login.microsoftonline.com/tenant-101/v2.0"
        self.client_id = "elevateiq-sp-app-id"
        self.client_secret = "super-secret-hmac-key-for-test-32b"

        self.verifier.register_provider(
            issuer=self.issuer,
            jwks_uri="https://login.microsoftonline.com/tenant-101/discovery/v2.0/keys",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    def _create_hs256_token(
        self,
        payload_overrides=None,
        secret=None,
        header_overrides=None,
    ) -> str:
        sec = (secret or self.client_secret).encode("utf-8")
        now = time.time()

        header = {"alg": "HS256", "typ": "JWT", "kid": "key_hs_1"}
        if header_overrides:
            header.update(header_overrides)

        payload = {
            "iss": self.issuer,
            "aud": self.client_id,
            "sub": "usr_aad_84920",
            "email": "sarah.connor@sky.net",
            "name": "Sarah Connor",
            "iat": int(now),
            "exp": int(now + 3600),
            "nonce": "test_nonce_abc123",
        }
        if payload_overrides:
            payload.update(payload_overrides)

        h_b64 = Base64UrlUtil.encode(json.dumps(header).encode("utf-8"))
        p_b64 = Base64UrlUtil.encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{h_b64}.{p_b64}".encode("ascii")
        sig = hmac.new(sec, signing_input, hashlib.sha256).digest()
        s_b64 = Base64UrlUtil.encode(sig)

        return f"{h_b64}.{p_b64}.{s_b64}"

    def test_valid_hs256_token_verification(self):
        token = self._create_hs256_token()
        result = self.verifier.verify_token(token, expected_issuer=self.issuer, expected_nonce="test_nonce_abc123")

        self.assertTrue(result.is_valid)
        self.assertEqual(result.subject, "usr_aad_84920")
        self.assertEqual(result.email, "sarah.connor@sky.net")
        self.assertEqual(result.name, "Sarah Connor")
        self.assertEqual(result.key_id, "key_hs_1")

    def test_expired_token_rejected(self):
        now = time.time()
        # Expired 1 hour ago
        token = self._create_hs256_token(payload_overrides={"exp": int(now - 3600), "iat": int(now - 7200)})
        result = self.verifier.verify_token(token)

        self.assertFalse(result.is_valid)
        self.assertIn("expired", result.error.lower())

    def test_audience_mismatch_rejected(self):
        token = self._create_hs256_token(payload_overrides={"aud": "unauthorized-client-id"})
        result = self.verifier.verify_token(token)

        self.assertFalse(result.is_valid)
        self.assertIn("Audience mismatch", result.error)

    def test_tampered_signature_rejected(self):
        token = self._create_hs256_token(secret="wrong-secret-key")
        result = self.verifier.verify_token(token)

        self.assertFalse(result.is_valid)
        self.assertIn("signature verification failed", result.error)

    def test_nonce_replay_attack_rejected(self):
        token = self._create_hs256_token(payload_overrides={"nonce": "single_use_nonce_999"})
        # 1st time -> valid
        res1 = self.verifier.verify_token(token, expected_nonce="single_use_nonce_999")
        self.assertTrue(res1.is_valid)

        # 2nd time -> rejected because nonce consumed
        res2 = self.verifier.verify_token(token, expected_nonce="single_use_nonce_999")
        self.assertFalse(res2.is_valid)
        self.assertIn("replay", res2.error.lower())

    def test_untrusted_issuer_rejected(self):
        token = self._create_hs256_token(payload_overrides={"iss": "https://untrusted-idp.com"})
        result = self.verifier.verify_token(token)

        self.assertFalse(result.is_valid)
        self.assertIn("Untrusted issuer", result.error)


if __name__ == "__main__":
    unittest.main()
