"""
ElevateIQ Enterprise Security Suite — Automated Unit Test Suite
================================================================
Tests Enterprise SSO (Google, Azure AD, Okta SAML), DLP Scanner,
IP CIDR Restriction Rules, User Session Revocation, and SOC2 Audit Logs.
"""

import unittest
import time
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, SecurityAuditLog, IPRestrictionRule, DLPOffenseLog
from backend.services.dlp_scanner import DLPScannerService


class EnterpriseSecurityTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                username="secadmin",
                email="admin@sec.example.com",
                display_name="Security Admin"
            )
            self.user.set_password("Password123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        # Login and obtain access token
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "secadmin",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_sso_providers_list_and_logins(self):
        # 1. List Providers
        res = self.client.get("/api/v1/auth/sso/providers")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 3)

        # 2. Google SSO Login
        res_g = self.client.post("/api/v1/auth/sso/google", json={
            "email": "employee@company.com",
            "name": "Employee User"
        })
        self.assertEqual(res_g.status_code, 200)
        self.assertIn("access_token", res_g.get_json())

        # 3. Azure AD SSO Login
        res_az = self.client.post("/api/v1/auth/sso/azure", json={
            "email": "executive@company.com",
            "name": "Executive User"
        })
        self.assertEqual(res_az.status_code, 200)

    def test_dlp_scanner_service(self):
        clean_text = "Hello team, let us review the meeting agenda."
        res_clean = DLPScannerService.scan_text(clean_text)
        self.assertTrue(res_clean["is_clean"])

        dirty_text = "Here is my SSN 123-45-6789 and AWS key aws_secret_access_key='12345678901234567890'"
        res_dirty = DLPScannerService.scan_text(dirty_text)
        self.assertFalse(res_dirty["is_clean"])
        self.assertEqual(len(res_dirty["offenses"]), 2)
        self.assertIn("[REDACTED BY ELEVATEIQ DLP]", res_dirty["redacted_text"])

    def test_security_audit_and_ip_rules(self):
        # 1. Add IP CIDR restriction rule
        res_ip = self.client.post("/api/security/ip-rules", json={
            "cidr_range": "10.0.0.0/16",
            "description": "Corporate VPN Network"
        }, headers=self.headers)
        self.assertEqual(res_ip.status_code, 201)

        # 2. Revoke user session
        res_rev = self.client.post("/api/security/revoke-session", json={
            "user_id": self.user_id
        }, headers=self.headers)
        self.assertEqual(res_rev.status_code, 200)

        # 3. Trigger DLP scan via REST endpoint
        res_dlp = self.client.post("/api/security/dlp-scan", json={
            "text_content": "Leaking SSN 987-65-4321 in file upload",
            "source": "file_upload"
        }, headers=self.headers)
        self.assertEqual(res_dlp.status_code, 200)

        # 4. Get SOC2 audit logs
        res_audit = self.client.get("/api/security/audit-logs", headers=self.headers)
        self.assertEqual(res_audit.status_code, 200)
        self.assertTrue(len(res_audit.get_json()) > 0)


if __name__ == "__main__":
    unittest.main()
