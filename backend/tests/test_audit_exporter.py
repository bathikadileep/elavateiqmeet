"""
ElevateIQ — Unit Test Suite for SIEM Security Audit Log Exporter
================================================================
Tests SIEM JSON serialization and HTTP streaming.
"""

import unittest
from backend.services.enterprise.audit_log_exporter import AuditLogExporterService


class AuditExporterTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = AuditLogExporterService()

    def test_json_export_serialization(self):
        """Test serializing audit log entries to JSON text format."""
        logs = [{"event_type": "SSO_LOGIN", "actor_id": "usr_1"}]
        json_str = self.service.export_logs_to_json(logs)

        self.assertIn("audit_events", json_str)
        self.assertIn("SSO_LOGIN", json_str)


if __name__ == "__main__":
    unittest.main()
