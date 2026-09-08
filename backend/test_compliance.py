"""
ElevateIQ — Unit & Integration Test Suite for GDPR, SSO & Audit Logging
=======================================================================
Executes automated test assertions covering:
  - GDPR Article 20 Zip Bundle Data Export
  - GDPR Article 17 Right to be Forgotten Anonymization
  - SAML 2.0 SP Metadata XML Generation
  - SHA-256 Hash Chained Security Audit Logging & Tamper Detection
"""

import unittest
import json
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, Role, UserRole, SecurityAuditLog
from backend.services.compliance_service import ComplianceService
from backend.services.sso_service import SSOService
from backend.services.audit_logger import AuditLoggerService


class ComplianceTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test user
        self.user = User(
            username="compliance_user",
            email="test_compliance@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Compliance Test User",
            status="active",
            email_verified=True,
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_gdpr_export_data_bundle(self):
        """Test GDPR Article 20 zip archive data export generation."""
        zip_bytes = ComplianceService.export_user_data_bundle(self.user.id)
        self.assertIsNotNone(zip_bytes)
        self.assertGreater(len(zip_bytes), 100)

    def test_gdpr_right_to_be_forgotten(self):
        """Test GDPR Article 17 account anonymization and data purging."""
        result = ComplianceService.execute_right_to_be_forgotten(self.user.id)
        self.assertEqual(result["status"], "success")
        
        # Verify user account anonymization
        updated_user = db.session.get(User, self.user.id)
        self.assertTrue(updated_user.username.startswith("deleted_user_"))
        self.assertTrue(updated_user.email.endswith("@privacy.deleted"))
        self.assertEqual(updated_user.display_name, "Deactivated Account")
        self.assertTrue(updated_user.is_deleted)

    def test_saml_sp_metadata_generation(self):
        """Test SAML 2.0 Service Provider Metadata XML layout."""
        metadata = SSOService.generate_saml_sp_metadata("https://elevateiq.com/sp", "https://elevateiq.com/acs")
        self.assertIn("EntityDescriptor", metadata)
        self.assertIn("AssertionConsumerService", metadata)
        self.assertIn("https://elevateiq.com/acs", metadata)

    def test_sha256_audit_log_hash_chaining(self):
        """Test cryptographic SHA-256 hash chaining and tamper detection."""
        log1 = AuditLoggerService.record_audit_event("user.login", self.user.id, "127.0.0.1", {"method": "password"})
        log2 = AuditLoggerService.record_audit_event("meeting.create", self.user.id, "127.0.0.1", {"code": "abc-1234-def"})

        self.assertIn("_crypto_entry_hash", log1.details)
        self.assertIn("_crypto_entry_hash", log2.details)
        self.assertEqual(log2.details["_crypto_prev_hash"], log1.details["_crypto_entry_hash"])

        # Verify integrity check passes
        integrity = AuditLoggerService.verify_audit_trail_integrity()
        self.assertEqual(integrity["chain_integrity_status"], "VALID")
        self.assertEqual(integrity["tampered_records_count"], 0)


if __name__ == "__main__":
    unittest.main()
