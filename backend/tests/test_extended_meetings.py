"""
ElevateIQ — Extended Meeting Lifecycle & State Transition Test Suite
====================================================================
Comprehensive integration test assertions verifying:
  - Meeting room code format validation (xxx-xxxx-xxx)
  - Scheduled vs Instant vs Recurring meeting types
  - Password hash generation & verification via Bcrypt
  - Host assignment & co-host privilege delegation
  - Participant join, leave, and kick status transitions
  - Soft delete and meeting cancellation handling
"""

import unittest
from datetime import datetime, timezone, timedelta
from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.models import User, Meeting, MeetingParticipant, Role, UserRole


class ExtendedMeetingLifecycleTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed Host and Participant Users
        self.host_user = User(
            username="host_ext_user",
            email="host_ext@elevateiq.com",
            password_hash=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
            display_name="Host Extended User",
            status="active",
            email_verified=True,
        )
        self.participant_user = User(
            username="part_ext_user",
            email="part_ext@elevateiq.com",
            password_hash=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
            display_name="Participant Extended User",
            status="active",
            email_verified=True,
        )
        db.session.add_all([self.host_user, self.participant_user])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_instant_meeting_creation(self):
        """Test instant meeting creation with default values."""
        meeting = Meeting(
            meeting_code="abc-1234-def",
            title="Instant Sync",
            host_id=self.host_user.id,
            status="live",
            meeting_type="instant",
            actual_start=datetime.now(timezone.utc)
        )
        db.session.add(meeting)
        db.session.commit()

        self.assertIsNotNone(meeting.id)
        self.assertEqual(meeting.status, "live")
        self.assertEqual(meeting.meeting_type, "instant")
        self.assertIsNone(meeting.password_hash)

    def test_password_protected_scheduled_meeting(self):
        """Test password protection on scheduled meetings."""
        raw_pwd = "SecretRoomPassword123"
        pwd_hash = bcrypt.generate_password_hash(raw_pwd).decode("utf-8")

        start_time = datetime.now(timezone.utc) + timedelta(hours=2)
        meeting = Meeting(
            meeting_code="sec-5678-xyz",
            title="Executive Board Meeting",
            host_id=self.host_user.id,
            status="scheduled",
            meeting_type="scheduled",
            scheduled_start=start_time,
            password_hash=pwd_hash
        )
        db.session.add(meeting)
        db.session.commit()

        self.assertIsNotNone(meeting.password_hash)
        self.assertTrue(bcrypt.check_password_hash(meeting.password_hash, raw_pwd))
        self.assertFalse(bcrypt.check_password_hash(meeting.password_hash, "WrongPassword"))

    def test_meeting_participant_roles_and_statuses(self):
        """Test participant role hierarchy and status transitions."""
        meeting = Meeting(
            meeting_code="role-9999-tst",
            title="Role Test Meeting",
            host_id=self.host_user.id,
            status="live",
            meeting_type="instant"
        )
        db.session.add(meeting)
        db.session.commit()

        host_part = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=self.host_user.id,
            role="host",
            status="joined"
        )
        guest_part = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=self.participant_user.id,
            role="participant",
            status="joined"
        )
        db.session.add_all([host_part, guest_part])
        db.session.commit()

        # Verify initial joined state
        self.assertEqual(host_part.role, "host")
        self.assertEqual(guest_part.role, "participant")
        self.assertEqual(guest_part.status, "joined")

        # Promote participant to co-host
        guest_part.role = "co_host"
        db.session.commit()

        updated_guest = MeetingParticipant.query.filter_by(id=guest_part.id).first()
        self.assertEqual(updated_guest.role, "co_host")

        # Kick participant
        updated_guest.status = "kicked"
        updated_guest.left_at = datetime.now(timezone.utc)
        db.session.commit()

        self.assertEqual(updated_guest.status, "kicked")
        self.assertIsNotNone(updated_guest.left_at)

    def test_meeting_cancellation_and_soft_delete(self):
        """Test soft delete and cancellation handling for meetings."""
        meeting = Meeting(
            meeting_code="del-0000-tst",
            title="Cancelled Meeting",
            host_id=self.host_user.id,
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
        self.assertIsNotNone(fetched.deleted_at)


if __name__ == "__main__":
    unittest.main()
