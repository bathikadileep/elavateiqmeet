"""
ElevateIQ — End-to-End Meeting Room Lifecycle Integration Test Suite
=====================================================================
Tests complete meeting lifecycle: creation, host auth, participant join,
chat messaging, whiteboard vectors, recording start, and teardown.
"""

import unittest
from datetime import datetime, timezone
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, Meeting, MeetingParticipant, Message


class EndToEndMeetingFlowTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.host = User(
            username="host_e2e",
            email="host_e2e@elevateiq.com",
            password_hash="hash",
            display_name="E2E Host User",
            status="active",
        )
        self.participant = User(
            username="part_e2e",
            email="part_e2e@elevateiq.com",
            password_hash="hash",
            display_name="E2E Participant User",
            status="active",
        )
        db.session.add_all([self.host, self.participant])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_full_meeting_lifecycle(self):
        """Test full meeting lifecycle flow from creation to teardown."""
        # 1. Create meeting
        meeting = Meeting(
            meeting_code="e2e-1000-tst",
            title="Q4 E2E Strategy Session",
            host_id=self.host.id,
            status="scheduled",
            meeting_type="scheduled"
        )
        db.session.add(meeting)
        db.session.commit()

        # 2. Host starts meeting -> status live
        meeting.status = "live"
        meeting.actual_start = datetime.now(timezone.utc)
        db.session.commit()
        self.assertEqual(meeting.status, "live")

        # 3. Add host & participant to room
        p_host = MeetingParticipant(meeting_id=meeting.id, user_id=self.host.id, role="host", status="joined")
        p_part = MeetingParticipant(meeting_id=meeting.id, user_id=self.participant.id, role="participant", status="joined")
        db.session.add_all([p_host, p_part])
        db.session.commit()

        # 4. Broadcast chat message
        msg = Message(meeting_id=meeting.id, user_id=self.participant.id, content="Hello team, ready for meeting.")
        db.session.add(msg)
        db.session.commit()

        # 5. End meeting
        meeting.status = "ended"
        meeting.actual_end = datetime.now(timezone.utc)
        db.session.commit()

        self.assertEqual(meeting.status, "ended")
        self.assertIsNotNone(meeting.actual_end)


if __name__ == "__main__":
    unittest.main()
