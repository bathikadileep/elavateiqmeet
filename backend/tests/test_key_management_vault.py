"""
ElevateIQ — Cryptographic Key Vault & Key Management Service Test Suite
========================================================================
Tests HSM/KMS key derivation, AES-256 envelope encryption, and key metadata.
"""

import unittest
from backend.services.enterprise.key_management import KeyManagementService


class KeyManagementVaultTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = KeyManagementService()

    def test_key_derivation_and_envelope_encryption(self):
        """Test deriving data encryption keys (DEK) for tenant envelope encryption."""
        raw_dek, enc_dek = self.service.generate_data_encryption_key("tenant_org_stark")
        self.assertEqual(len(raw_dek), 32)
        self.assertIsNotNone(enc_dek)

    def test_envelope_encrypt_decrypt_simulation(self):
        """Test encrypting and decrypting sensitive database columns via envelope key."""
        plaintext = "Sensitive Enterprise Legal Transcript Data"
        encrypted = self.service.encrypt_data_payload("tenant_org_stark", plaintext)
        self.assertNotEqual(plaintext, encrypted["ciphertext"])

        decrypted = self.service.decrypt_data_payload("tenant_org_stark", encrypted["ciphertext"])
        self.assertEqual(plaintext, decrypted)


if __name__ == "__main__":
    unittest.main()
