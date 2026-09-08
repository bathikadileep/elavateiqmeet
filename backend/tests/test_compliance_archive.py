"""
ElevateIQ — Unit Test Suite for Compliance Archive & Legal Hold Engine
========================================================================
Tests WORM immutable hashing, legal hold application/release, and retention policy purging eligibility.
"""

import unittest
from backend.services.compliance_archive_service import ComplianceArchiveService


class ComplianceArchiveTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = ComplianceArchiveService(default_retention_days=30)

    def test_archive_artifacts_with_checksum(self):
        """Test archiving meeting artifacts with SHA-256 checksum."""
        entry = self.service.archive_meeting_artifacts(
            meeting_code="room-arch-101",
            recording_url="https://s3.aws.com/rec.mp4",
            transcript_text="Full meeting transcript text sample.",
            audit_logs_count=15
        )

        self.assertEqual(entry["meeting_code"], "room-arch-101")
        self.assertTrue(entry["is_worm_locked"])
        self.assertIsNotNone(entry["checksum_sha256"])

    def test_legal_hold_freeze_lifecycle(self):
        """Test applying and releasing legal hold freezes on archives."""
        self.service.archive_meeting_artifacts("room-arch-101", None, "test", 2)
        hold = self.service.apply_legal_hold("room-arch-101", "CASE-2026-90", "FINRA Audit Investigation", "admin_user")

        self.assertTrue(hold["is_active"])
        self.assertFalse(self.service.is_eligible_for_purging("room-arch-101"))

        released = self.service.release_legal_hold("room-arch-101", "CASE-2026-90")
        self.assertTrue(released)


if __name__ == "__main__":
    unittest.main()
