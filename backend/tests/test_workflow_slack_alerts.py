"""
ElevateIQ — Unit Test Suite for Slack & CRM Workflow Alerts
============================================================
Tests Slack channel notification dispatches and automated CRM post-meeting sync triggers.
"""

import unittest
from backend.services.workflow_automation import WorkflowAutomationEngine


class WorkflowSlackAlertsTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = WorkflowAutomationEngine()

    def test_slack_alert_workflow_execution(self):
        """Test triggering Slack notification workflow upon meeting end."""
        self.engine.register_workflow(
            workflow_id="wf_slack_summary",
            trigger_event="meeting.ended",
            target_action="SLACK_ALERT",
            payload_template={"channel": "#meeting-notes"}
        )

        res = self.engine.handle_event_trigger("meeting.ended", {"meeting_code": "room-slack-101"})
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["status"], "SUCCESS")

    def test_crm_sync_workflow_execution(self):
        """Test triggering CRM sync workflow upon summary generation."""
        self.engine.register_workflow(
            workflow_id="wf_crm_sync",
            trigger_event="summary.generated",
            target_action="CRM_SYNC",
            payload_template={"crm": "Salesforce"}
        )

        res = self.engine.handle_event_trigger("summary.generated", {"meeting_code": "room-crm-202"})
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
