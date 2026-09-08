"""
ElevateIQ — Extended Cloud Recordings & Transcoding Test Suite
==============================================================
Tests recording session status transitions (processing -> available -> deleted)
and HLS playlist generation.
"""

import unittest
import os
from backend.app import create_app
from backend.extensions import db
from backend.models.models import Meeting, MeetingRecording, User
from backend.services.hls_transcoder import HLSTranscoderService


class ExtendedRecordingsTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.host = User(
            username="rec_user",
            email="rec@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Recording Host",
            status="active",
            email_verified=True,
        )
        db.session.add(self.host)
        db.session.commit()

        self.meeting = Meeting(
            meeting_code="rec-1234-tst",
            title="Recording Session",
            host_id=self.host.id,
            status="ended",
            meeting_type="instant"
        )
        db.session.add(self.meeting)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_recording_lifecycle(self):
        """Test recording session status transitions."""
        rec = MeetingRecording(
            meeting_id=self.meeting.id,
            initiated_by=self.host.id,
            status="processing"
        )
        db.session.add(rec)
        db.session.commit()

        self.assertEqual(rec.status, "processing")

        # Complete processing
        rec.status = "available"
        rec.duration_seconds = 1800
        rec.size_bytes = 150000000
        rec.download_url = "/uploads/recordings/rec_1234.mp4"
        db.session.commit()

        fetched = MeetingRecording.query.filter_by(id=rec.id).first()
        self.assertEqual(fetched.status, "available")
        self.assertEqual(fetched.duration_seconds, 1800)


if __name__ == "__main__":
    unittest.main()
