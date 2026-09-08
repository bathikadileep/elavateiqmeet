"""
ElevateIQ — Unit Test Suite for Compliance Retention Purging Eligibility
========================================================================
Tests retention expiration cutoff logic and legal hold override checks.
"""

import unittest
from backend.services.compliance_archive_service import ComplianceArchiveService


class CompliancePurgingTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = ComplianceArchiveService(default_retention_days=0)  # Immediate expiration for testing

    def test_purging_eligibility_without_legal_hold(self):
        """Test archive expired cutoff without legal hold is eligible for purging."""
        self.service.archive_meeting_artifacts("room-purge-101", "http://rec.mp4", "transcript", 5)
        self.assertTrue(self.service.is_eligible_for_purging("room-purge-101"))

    def test_legal_hold_blocks_purging(self):
        """Test applying legal hold blocks purging eligibility even if retention expired."""
        self.service.archive_meeting_artifacts("room-purge-202", "http://rec.mp4", "transcript", 5)
        self.service.apply_legal_hold("room-purge-202", "CASE-999", "Audit", "admin")
        self.assertFalse(self.service.is_eligible_for_purging("room-purge-202"))


if __name__ == "__main__":
    unittest.main()
