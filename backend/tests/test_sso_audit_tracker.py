"""
ElevateIQ — Unit Test Suite for SSO Security Audit Tracker
==========================================================
Tests logging SSO events and retrieving audit trails for user ID.
"""

import unittest
from backend.services.enterprise.sso_audit_tracker import SSOAuditTracker


class SSOAuditTrackerTestSuite(unittest.TestCase):

    def setUp(self):
        self.tracker = SSOAuditTracker()

    def test_record_and_query_sso_event(self):
        """Test recording SSO login audit entry."""
        evt = self.tracker.record_sso_event("SSO_LOGIN", "usr_101", "Okta", "192.168.1.1")
        self.assertEqual(evt["status"], "SUCCESS")

        events = self.tracker.get_events_for_user("usr_101")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["provider"], "Okta")


if __name__ == "__main__":
    unittest.main()
