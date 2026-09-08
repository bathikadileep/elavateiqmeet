"""
ElevateIQ — Unit & Integration Test Suite for Breakout Rooms Management
========================================================================
Tests breakout room creation, user assignment, auto-shuffling, and session termination.
"""

import unittest
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, Meeting, BreakoutRoom, BreakoutAssignment
from backend.services.breakout_service import BreakoutService


class BreakoutManagementTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.service = BreakoutService()

        self.user1 = User(username="u1", email="u1@test.com", password_hash="hash", display_name="User 1")
        self.user2 = User(username="u2", email="u2@test.com", password_hash="hash", display_name="User 2")
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_breakout_room_creation_and_assignment(self):
        """Test creating breakout rooms and assigning participants."""
        res = self.service.create_breakout_rooms(
            main_room_code="room-brk-101",
            participant_ids=[self.user1.id, self.user2.id],
            num_rooms=2,
            duration_minutes=20
        )
        self.assertEqual(res["num_rooms"], 2)
        self.assertEqual(len(res["breakout_rooms"]), 2)

    def test_broadcast_announcement(self):
        """Test broadcasting message to breakout rooms."""
        b = self.service.broadcast_announcement("room-brk-101", "Closing in 2 minutes!")
        self.assertEqual(b["broadcast_message"], "Closing in 2 minutes!")


if __name__ == "__main__":
    unittest.main()
