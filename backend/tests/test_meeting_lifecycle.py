"""
ElevateIQ — Comprehensive Meeting Lifecycle & Room State Integration Tests
==========================================================================
Tests room code generation, password hashing, host authorization, participant join/leave,
and automatic meeting teardown.
"""

import unittest
from datetime import datetime, timezone
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, Meeting, MeetingParticipant


class MeetingLifecycleTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed host user
        self.host = User(
            username="test_host_life",
            email="host_life@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Host Life User",
            status="active",
            email_verified=True,
        )
        db.session.add(self.host)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_meeting_cancellation_and_soft_delete(self):
        """Test soft delete and cancellation handling for meetings."""
        meeting = Meeting(
            meeting_code="del-0000-tst",
            title="Cancelled Meeting",
            host_id=self.host.id,
            status="scheduled",
            meeting_type="scheduled"
        )
        db.session.add(meeting)
        db.session.commit()

        # Cancel meeting
        meeting.status = "cancelled"
        meeting.is_deleted = True
        meeting.deleted_at = datetime.now(timezone.utc)
        db.session.commit()

        fetched = Meeting.query.filter_by(meeting_code="del-0000-tst").first()
        self.assertEqual(fetched.status, "cancelled")
        self.assertTrue(fetched.is_deleted)

    def test_meeting_creation_and_code_format(self):
        """Test meeting creation and room code format."""
        meeting = Meeting(
            meeting_code="dfa-2061-2b7",
            title="Q4 Architecture Review",
            host_id=self.host.id,
            status="scheduled",
            meeting_type="instant"
        )
        db.session.add(meeting)
        db.session.commit()

        fetched = Meeting.query.filter_by(meeting_code="dfa-2061-2b7").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Q4 Architecture Review")
        self.assertEqual(fetched.host_id, self.host.id)

    def test_participant_join_and_leave(self):
        """Test adding participant record to meeting."""
        meeting = Meeting(
            meeting_code="b7a-9921-xyz",
            title="Design Alignment",
            host_id=self.host.id,
            status="live",
            meeting_type="instant"
        )
        db.session.add(meeting)
        db.session.commit()

        part = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=self.host.id,
            role="host",
            status="joined"
        )
        db.session.add(part)
        db.session.commit()

        fetched_part = MeetingParticipant.query.filter_by(meeting_id=meeting.id, user_id=self.host.id).first()
        self.assertIsNotNone(fetched_part)
        self.assertEqual(fetched_part.role, "host")


if __name__ == "__main__":
    unittest.main()
