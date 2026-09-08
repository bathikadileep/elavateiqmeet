"""
ElevateIQ — Unit Test Suite for Virtual Lobby Passcode Verification
====================================================================
Tests pre-entry password validation and host guest admission logic.
"""

import unittest
from backend.extensions import bcrypt
from backend.services.virtual_lobby_service import VirtualLobbyService


class VirtualLobbyPasscodeTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = VirtualLobbyService()

    def test_passcode_validation(self):
        """Test guest room passcode verification before joining queue."""
        raw_passcode = "SecretPass123"
        hashed = bcrypt.generate_password_hash(raw_passcode).decode("utf-8")

        valid = self.service.evaluate_guest_passcode("room-pass-101", "usr_guest", raw_passcode, hashed)
        self.assertTrue(valid)

        invalid = self.service.evaluate_guest_passcode("room-pass-101", "usr_guest", "WrongPass", hashed)
        self.assertFalse(invalid)


if __name__ == "__main__":
    unittest.main()
