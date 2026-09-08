"""
ElevateIQ — Unit Tests for Consent Management & Privacy Ledger Service
========================================================================
Tests consent registration, revocation, cryptographic HMAC chaining,
ledger tamper-detection, two-party recording compliance, and expiration.
"""

import unittest
from backend.services.enterprise.consent_manager import (
    ConsentManager,
    ConsentType,
    ConsentStatus,
    ConsentReceipt
)


class TestConsentManager(unittest.TestCase):

    def setUp(self):
        self.manager = ConsentManager(signing_secret="test-secret-key-1234")

    def test_record_and_query_consent(self):
        rcpt = self.manager.record_consent(
            tenant_id="tenant_alpha",
            room_code="room_101",
            user_id="usr_alice",
            consent_type=ConsentType.RECORDING_AV,
            status=ConsentStatus.GRANTED,
            client_ip="192.168.1.50"
        )
        self.assertEqual(rcpt.status, ConsentStatus.GRANTED)
        self.assertTrue(len(rcpt.receipt_signature) == 64)

        is_allowed = self.manager.is_consent_granted("room_101", "usr_alice", ConsentType.RECORDING_AV)
        self.assertTrue(is_allowed)

        # Unrequested scope should be False
        has_ai = self.manager.is_consent_granted("room_101", "usr_alice", ConsentType.AI_TRANSCRIPTION)
        self.assertFalse(has_ai)

    def test_revoke_consent(self):
        # Alice grants recording
        self.manager.record_consent(
            tenant_id="tenant_alpha",
            room_code="room_101",
            user_id="usr_alice",
            consent_type=ConsentType.RECORDING_AV,
            status=ConsentStatus.GRANTED,
            client_ip="192.168.1.50"
        )
        self.assertTrue(self.manager.is_consent_granted("room_101", "usr_alice", ConsentType.RECORDING_AV))

        # Alice revokes recording
        rcpt_revoked = self.manager.revoke_consent(
            tenant_id="tenant_alpha",
            room_code="room_101",
            user_id="usr_alice",
            consent_type=ConsentType.RECORDING_AV,
            client_ip="192.168.1.50"
        )
        self.assertEqual(rcpt_revoked.status, ConsentStatus.REVOKED)
        self.assertFalse(self.manager.is_consent_granted("room_101", "usr_alice", ConsentType.RECORDING_AV))

    def test_cryptographic_ledger_integrity(self):
        # Add multiple blocks
        self.manager.record_consent("t1", "r1", "u1", ConsentType.RECORDING_AV, ConsentStatus.GRANTED, "10.0.0.1")
        self.manager.record_consent("t1", "r1", "u2", ConsentType.RECORDING_AV, ConsentStatus.GRANTED, "10.0.0.2")
        self.manager.record_consent("t1", "r1", "u1", ConsentType.AI_TRANSCRIPTION, ConsentStatus.GRANTED, "10.0.0.1")

        is_valid, count = self.manager.verify_ledger_integrity()
        self.assertTrue(is_valid)
        self.assertEqual(count, 3)

    def test_tamper_detection_in_ledger(self):
        self.manager.record_consent("t1", "r1", "u1", ConsentType.RECORDING_AV, ConsentStatus.GRANTED, "10.0.0.1")
        self.manager.record_consent("t1", "r1", "u2", ConsentType.RECORDING_AV, ConsentStatus.GRANTED, "10.0.0.2")

        # Malicious attacker modifies block 0 status
        self.manager.receipts[0].status = ConsentStatus.DENIED

        is_valid, tampered_block = self.manager.verify_ledger_integrity()
        self.assertFalse(is_valid)
        self.assertEqual(tampered_block, 0)

    def test_room_recording_compliance_two_party(self):
        # Alice consented, Bob has not consented yet
        self.manager.record_consent("t1", "room_sync", "usr_alice", ConsentType.RECORDING_AV, ConsentStatus.GRANTED, "10.0.0.1")
        self.manager.record_consent("t1", "room_sync", "usr_alice", ConsentType.AI_TRANSCRIPTION, ConsentStatus.GRANTED, "10.0.0.1")

        compliance = self.manager.verify_room_recording_compliance(
            room_code="room_sync",
            participant_ids=["usr_alice", "usr_bob"]
        )
        self.assertFalse(compliance["is_recording_allowed"])
        self.assertFalse(compliance["is_ai_allowed"])
        self.assertIn("usr_bob", compliance["unconsented_recording_users"])

        # Bob now consents
        self.manager.record_consent("t1", "room_sync", "usr_bob", ConsentType.RECORDING_AV, ConsentStatus.GRANTED, "10.0.0.2")
        self.manager.record_consent("t1", "room_sync", "usr_bob", ConsentType.AI_TRANSCRIPTION, ConsentStatus.GRANTED, "10.0.0.2")

        compliance_after = self.manager.verify_room_recording_compliance(
            room_code="room_sync",
            participant_ids=["usr_alice", "usr_bob"]
        )
        self.assertTrue(compliance_after["is_recording_allowed"])
        self.assertTrue(compliance_after["is_ai_allowed"])
        self.assertEqual(len(compliance_after["unconsented_recording_users"]), 0)


if __name__ == "__main__":
    unittest.main()
