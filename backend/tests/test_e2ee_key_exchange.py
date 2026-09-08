"""
ElevateIQ — Unit Test Suite for End-to-End Encryption (E2EE) Key Exchange
========================================================================
Tests MLS session initialization, group epoch advancing, SFrame key derivation, and forward secrecy rekeying.
"""

import unittest
from backend.services.e2ee_key_exchange import E2EEKeyExchangeService


class E2EEKeyExchangeTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = E2EEKeyExchangeService()

    def test_room_session_initialization(self):
        """Test initializing E2EE group context."""
        session = self.service.initialize_room_session("room-e2ee-101", "peer_host_1")
        self.assertEqual(session["meeting_code"], "room-e2ee-101")
        self.assertEqual(session["epoch"], 1)
        self.assertIn("peer_host_1", session["participants"])

    def test_epoch_advancement_on_join(self):
        """Test group epoch increment and key package integration."""
        self.service.initialize_room_session("room-e2ee-101", "peer_host_1")
        res = self.service.add_participant_key_package("room-e2ee-101", "peer_guest_2", "b64_key_pkg_sample_123")

        self.assertEqual(res["epoch"], 2)
        self.assertIsNotNone(res["ratchet_tree_hash"])

    def test_sframe_frame_key_derivation(self):
        """Test deriving WebRTC SFrame 32-byte AES key and 12-byte IV."""
        self.service.initialize_room_session("room-e2ee-101", "peer_host_1")
        key, iv = self.service.generate_frame_encryption_key("room-e2ee-101", "peer_host_1", frame_index=42)

        self.assertEqual(len(key), 32)
        self.assertEqual(len(iv), 12)

    def test_forward_secrecy_rekey_on_eviction(self):
        """Test immediate forward-secrecy rekeying upon evicted participant."""
        self.service.initialize_room_session("room-e2ee-101", "peer_host_1")
        self.service.add_participant_key_package("room-e2ee-101", "peer_guest_2", "pkg_2")

        rekey_res = self.service.remove_participant_and_rekey("room-e2ee-101", "peer_guest_2")
        self.assertEqual(rekey_res["status"], "REKEYED")
        self.assertEqual(rekey_res["epoch"], 3)
        self.assertEqual(rekey_res["remaining_participants"], 1)


if __name__ == "__main__":
    unittest.main()
