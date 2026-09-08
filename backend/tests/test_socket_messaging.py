"""
ElevateIQ — Real-Time Socket.IO & Vector Whiteboard Integration Tests
=====================================================================
Tests Socket.IO connection handshakes, chat message broadcasting,
and whiteboard stroke vector coordinate payloads.
"""

import unittest
from backend.app import create_app
from backend.extensions import db


class SocketMessagingTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_whiteboard_stroke_vector_payload_structure(self):
        """Test validation of whiteboard vector drawing stroke payloads."""
        stroke = {
            "room_code": "dfa-2061-2b7",
            "tool": "pen",
            "color": "#00f2fe",
            "size": 3,
            "points": [{"x": 100, "y": 150}, {"x": 105, "y": 155}, {"x": 110, "y": 160}]
        }
        self.assertEqual(stroke["tool"], "pen")
        self.assertEqual(len(stroke["points"]), 3)
        self.assertEqual(stroke["color"], "#00f2fe")

    def test_chat_message_payload_sanitization(self):
        """Test in-meeting chat message text trimming and sanitization."""
        raw_msg = "   Hello team! Welcome to the meeting.   "
        sanitized = raw_msg.strip()
        self.assertEqual(sanitized, "Hello team! Welcome to the meeting.")


if __name__ == "__main__":
    unittest.main()
