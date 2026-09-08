"""
ElevateIQ — Unit Test Suite for Workflow Automation & Webhook Engine
=====================================================================
Tests workflow registration, trigger matching, payload merging, and execution logging.
"""

import unittest
from backend.services.workflow_automation import WorkflowAutomationEngine


class WorkflowAutomationTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = WorkflowAutomationEngine()

    def test_workflow_registration_and_listing(self):
        """Test registering workflow triggers and retrieving active rules."""
        wf = self.engine.register_workflow(
            workflow_id="wf_slack_alert",
            trigger_event="meeting.ended",
            target_action="SLACK_ALERT",
            payload_template={"channel": "#meeting-summaries"}
        )

        self.assertEqual(wf["workflow_id"], "wf_slack_alert")
        self.assertEqual(wf["trigger_event"], "meeting.ended")

        active = self.engine.list_workflows("meeting.ended")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["workflow_id"], "wf_slack_alert")

    def test_event_trigger_execution(self):
        """Test executing workflows when a trigger event fires."""
        self.engine.register_workflow(
            workflow_id="wf_webhook_post",
            trigger_event="recording.available",
            target_action="WEBHOOK_POST",
            payload_template={},
            webhook_url="http://localhost:5000/webhook/test"
        )

        results = self.engine.handle_event_trigger("recording.available", {"recording_id": "rec_999"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "SUCCESS")
        self.assertEqual(results[0]["http_code"], 200)

        history = self.engine.get_execution_history()
        self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
