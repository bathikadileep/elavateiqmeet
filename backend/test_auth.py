"""
ElevateIQ — Authentication Module Unit & Integration Tests
=============================================================
Tests all 8 authentication endpoints:
  1. register
  2. login
  3. logout
  4. refresh
  5. me
  6. forgot-password
  7. reset-password
  8. change-password

Run:
    .\backend\venv\Scripts\python.exe -m unittest backend.test_auth -v
"""

import unittest
import json
from backend.app import create_app
from backend.extensions import db


class AuthTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _register(self, username="testuser", email="test@example.com",
                  password="password123", display_name="Test User"):
        return self.client.post(
            "/api/v1/auth/register",
            data=json.dumps({
                "username": username,
                "email": email,
                "password": password,
                "display_name": display_name,
            }),
            content_type="application/json",
        )

    def _login(self, identity="testuser", password="password123"):
        return self.client.post(
            "/api/v1/auth/login",
            data=json.dumps({"identity": identity, "password": password}),
            content_type="application/json",
        )

    # ── 1. Registration ───────────────────────────────────────────────────────

    def test_register_success(self):
        res = self._register()
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], "testuser")

    def test_register_missing_fields(self):
        res = self.client.post(
            "/api/v1/auth/register",
            data=json.dumps({"username": "only"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_register_duplicate_username(self):
        self._register()
        res = self._register()
        self.assertEqual(res.status_code, 409)

    def test_register_short_password(self):
        res = self._register(password="123")
        self.assertEqual(res.status_code, 400)

    # ── 2. Login ──────────────────────────────────────────────────────────────

    def test_login_success(self):
        self._register()
        res = self._login()
        self.assertEqual(res.status_code, 200)
        cookies_str = "; ".join(res.headers.getlist("Set-Cookie"))
        self.assertIn("access_token_cookie", cookies_str)

    def test_login_invalid_credentials(self):
        self._register()
        res = self._login(password="wrongpass")
        self.assertEqual(res.status_code, 401)

    # ── 3. Logout & Refresh ───────────────────────────────────────────────────

    def test_logout(self):
        self._register()
        self._login()
        res = self.client.post("/api/v1/auth/logout")
        self.assertEqual(res.status_code, 200)

    def test_token_refresh(self):
        self._register()
        self._login()
        res = self.client.post("/api/v1/auth/refresh")
        self.assertEqual(res.status_code, 200)

    # ── 4. Profile (me) ───────────────────────────────────────────────────────

    def test_me_authenticated(self):
        self._register()
        self._login()
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["user"]["username"], "testuser")

    def test_me_unauthenticated(self):
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 401)

    # ── 5. Forgot & Reset Password Flow ───────────────────────────────────────

    def test_forgot_and_reset_password_flow(self):
        self._register()

        # Step 1: Request forgot password
        forgot_res = self.client.post(
            "/api/v1/auth/forgot-password",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(forgot_res.status_code, 200)
        forgot_data = forgot_res.get_json()
        self.assertIn("reset_token", forgot_data)
        token = forgot_data["reset_token"]

        # Step 2: Reset password using token
        reset_res = self.client.post(
            "/api/v1/auth/reset-password",
            data=json.dumps({"token": token, "new_password": "newpassword123"}),
            content_type="application/json",
        )
        self.assertEqual(reset_res.status_code, 200)

        # Step 3: Verify login works with new password
        login_res = self._login(password="newpassword123")
        self.assertEqual(login_res.status_code, 200)

    def test_reset_password_invalid_token(self):
        res = self.client.post(
            "/api/v1/auth/reset-password",
            data=json.dumps({"token": "fake-token-123", "new_password": "newpassword123"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    # ── 6. Change Password (Authenticated) ────────────────────────────────────

    def test_change_password_success(self):
        self._register()
        self._login()

        change_res = self.client.post(
            "/api/v1/auth/change-password",
            data=json.dumps({
                "current_password": "password123",
                "new_password": "changedpassword123",
            }),
            content_type="application/json",
        )
        self.assertEqual(change_res.status_code, 200)

        # Confirm old password fails and new password succeeds
        self.assertEqual(self._login(password="password123").status_code, 401)
        self.assertEqual(self._login(password="changedpassword123").status_code, 200)

    def test_change_password_wrong_current(self):
        self._register()
        self._login()

        res = self.client.post(
            "/api/v1/auth/change-password",
            data=json.dumps({
                "current_password": "wrongpassword",
                "new_password": "changedpassword123",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
