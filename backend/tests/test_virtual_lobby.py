"""
ElevateIQ — Unit Test Suite for Virtual Waiting Room & Pre-Screening Lobby
==========================================================================
Tests joining lobby queues, host admit/deny decisions, and passcode evaluation.
"""

import unittest
from backend.extensions import bcrypt
from backend.services.virtual_lobby_service import VirtualLobbyService


class VirtualLobbyTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = VirtualLobbyService()

    def test_join_lobby_queue_and_retrieval(self):
        """Test placing guests into room waiting queue."""
        entry = self.service.join_lobby_queue(
            meeting_code="room-lobby-101",
            user_id="user_guest_1",
            display_name="Guest One",
            email="guest1@external.com"
        )

        self.assertEqual(entry["status"], "WAITING")
        self.assertEqual(entry["display_name"], "Guest One")

        waiting = self.service.get_waiting_guests("room-lobby-101")
        self.assertEqual(len(waiting), 1)

    def test_host_admit_and_deny_decisions(self):
        """Test host admitting and denying guest waiting room requests."""
        self.service.join_lobby_queue("room-lobby-101", "guest_1", "Guest 1")
        self.service.join_lobby_queue("room-lobby-101", "guest_2", "Guest 2")

        # Admit guest 1
        admit_res = self.service.process_host_decision("room-lobby-101", "guest_1", "host_user", "ADMIT")
        self.assertEqual(admit_res["status"], "ADMITTED")

        # Deny guest 2
        deny_res = self.service.process_host_decision("room-lobby-101", "guest_2", "host_user", "DENY")
        self.assertEqual(deny_res["status"], "DENIED")

        # No remaining waiting guests
        waiting = self.service.get_waiting_guests("room-lobby-101")
        self.assertEqual(len(waiting), 0)

    def test_host_admit_all(self):
        """Test host admitting all queued guests simultaneously."""
        self.service.join_lobby_queue("room-lobby-all", "g1", "Guest 1")
        self.service.join_lobby_queue("room-lobby-all", "g2", "Guest 2")

        res = self.service.process_host_decision("room-lobby-all", "", "host_user", "ADMIT_ALL")
        self.assertEqual(res["admitted_count"], 2)


if __name__ == "__main__":
    unittest.main()
