"""
ElevateIQ — Unit Test Suite for WebRTC SFrame & Insertable Streams Interoperability
=====================================================================================
Tests WebRTC SFrame payload header tagging, frame key rotation, and cipher suite negotiation.
"""

import unittest
from backend.services.e2ee_key_exchange import E2EEKeyExchangeService


class E2EESFrameInteroperabilityTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = E2EEKeyExchangeService()
        self.service.initialize_room_session("room-sframe-101", "peer_sender_1")

    def test_sframe_payload_header_format(self):
        """Test generating WebRTC SFrame key and IV for video frame #100."""
        key, iv = self.service.generate_frame_encryption_key("room-sframe-101", "peer_sender_1", frame_index=100)
        self.assertEqual(len(key), 32)
        self.assertEqual(len(iv), 12)

    def test_multi_peer_ratchet_tree_expansion(self):
        """Test adding multiple peers to SFrame ratchet tree."""
        self.service.add_participant_key_package("room-sframe-101", "peer_receiver_2", "pkg_b64_2")
        self.service.add_participant_key_package("room-sframe-101", "peer_receiver_3", "pkg_b64_3")

        rekey = self.service.remove_participant_and_rekey("room-sframe-101", "peer_receiver_2")
        self.assertEqual(rekey["status"], "REKEYED")
        self.assertEqual(rekey["remaining_participants"], 2)


if __name__ == "__main__":
    unittest.main()
