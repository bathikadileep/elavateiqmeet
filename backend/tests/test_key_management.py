"""
ElevateIQ — Unit Test Suite for KMS Envelope Encryption & Billing
===================================================================
Tests Data Encryption Key (DEK) generation, payload encryption/decryption,
and billing plan usage metering overage calculations.
"""

import unittest
from backend.services.enterprise.key_management import KeyManagementService
from backend.services.enterprise.billing_engine import BillingEngineService
from backend.services.enterprise.license_validator import LicenseValidatorService


class KMSBillingTestSuite(unittest.TestCase):

    def setUp(self):
        self.kms_service = KeyManagementService()
        self.billing_service = BillingEngineService()

    def test_kms_envelope_encryption_decryption(self):
        """Test KMS data payload encryption and decryption cycle."""
        key_id = "test-key-101"
        plaintext = "Confidential Enterprise Secret Data"

        encrypted_payload = self.kms_service.encrypt_data_payload(key_id, plaintext)
        self.assertEqual(encrypted_payload["key_id"], key_id)
        self.assertIn("ciphertext", encrypted_payload)

        decrypted = self.kms_service.decrypt_data_payload(key_id, encrypted_payload["ciphertext"])
        self.assertEqual(decrypted, plaintext)

    def test_billing_usage_metering_and_invoicing(self):
        """Test participant meeting minutes metering and overage invoice calculation."""
        tenant_id = "tenant_billing_test"
        self.billing_service.record_meeting_duration(tenant_id, duration_minutes=60, participant_count=50)

        invoice = self.billing_service.generate_invoice_summary(tenant_id)
        self.assertEqual(invoice["tenant_id"], tenant_id)
        self.assertGreaterEqual(invoice["total_due_usd"], 15.0)

    def test_license_key_generation_and_validation(self):
        """Test enterprise license key generation and cryptographic validation."""
        key = LicenseValidatorService.generate_license_key("Acme Global", max_seats=500, expiration_days=30, features=["sso", "ai"])
        self.assertTrue(key.startswith("ELIQ-"))

        validation = LicenseValidatorService.validate_license_key(key)
        self.assertTrue(validation["is_valid"])
        self.assertEqual(validation["customer"], "Acme Global")
        self.assertEqual(validation["max_seats"], 500)


if __name__ == "__main__":
    unittest.main()
