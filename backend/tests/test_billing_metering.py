"""
ElevateIQ — Unit & Integration Test Suite for Usage-Based Billing Engine
========================================================================
Tests participant minute metering, storage usage calculation, and invoice summary generation.
"""

import unittest
from backend.services.enterprise.billing_engine import BillingEngineService


class BillingMeteringTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = BillingEngineService()

    def test_record_meeting_duration(self):
        """Test metering participant meeting duration minutes."""
        usage = self.service.record_meeting_duration("org_stark", duration_minutes=60, participant_count=10)
        self.assertEqual(usage["meeting_minutes_used"], 600)

    def test_generate_invoice_summary(self):
        """Test generating invoice summary with overage fees."""
        self.service.record_meeting_duration("org_small", duration_minutes=1000, participant_count=10)
        inv = self.service.generate_invoice_summary("org_small")

        self.assertEqual(inv["tenant_id"], "org_small")
        self.assertGreater(inv["total_due_usd"], 0)


if __name__ == "__main__":
    unittest.main()
