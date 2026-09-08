"""
ElevateIQ — Unit Test Suite for Key Rotation Scheduler
======================================================
Tests evaluating automated cryptographic key rotation schedules.
"""

import unittest
from datetime import datetime, timezone, timedelta
from backend.services.enterprise.key_rotation_scheduler import KeyRotationScheduler


class KeyRotationSchedulerTestSuite(unittest.TestCase):

    def setUp(self):
        self.scheduler = KeyRotationScheduler()

    def test_schedule_evaluation(self):
        """Test rotation due check for 100 day old key vs 10 day old key."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        recent_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

        self.assertTrue(self.scheduler.evaluate_rotation_schedule(old_date, interval_days=90))
        self.assertFalse(self.scheduler.evaluate_rotation_schedule(recent_date, interval_days=90))


if __name__ == "__main__":
    unittest.main()
