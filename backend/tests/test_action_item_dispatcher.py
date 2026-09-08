"""
ElevateIQ — Unit Test Suite for Action Item Multi-Platform Dispatcher
=====================================================================
Tests dispatching action items to Jira, Asana, Linear, and Webhook endpoints,
retry exponential backoff logic, dead-letter queuing, and batch operations.
"""

import unittest
from backend.services.ai.action_item_dispatcher import (
    ActionItemDispatcher,
    ActionItemRecord,
    IntegrationPlatform,
    TaskPriority,
    DispatchStatus,
)


class ActionItemDispatcherTestSuite(unittest.TestCase):

    def setUp(self):
        self.dispatcher = ActionItemDispatcher()
        self.sample_item = ActionItemRecord(
            item_id="act_item_901",
            meeting_id="meet_q3_planning",
            title="Update database index on message_id column",
            description="Database query latency during 1000+ attendee webinars exceeds 200ms.",
            assignee_email="dev.lead@elevateiq.com",
            assignee_name="Marcus Vance",
            due_date_iso="2026-09-15",
            priority=TaskPriority.HIGH,
            tags=["database", "performance", "backend"],
        )

    def test_dispatch_to_jira_success(self):
        """Test successful dispatch to Jira Cloud REST format."""
        result = self.dispatcher.dispatch_item(self.sample_item, IntegrationPlatform.JIRA)

        self.assertEqual(result.status, DispatchStatus.SUCCESS)
        self.assertIsNotNone(result.external_task_id)
        self.assertTrue(result.external_task_id.startswith("ELVIQ-"))
        self.assertIn("atlassian.net", result.external_task_url)
        self.assertEqual(result.retry_count, 0)

    def test_dispatch_to_linear_success(self):
        """Test dispatching to Linear GraphQL format."""
        result = self.dispatcher.dispatch_item(self.sample_item, IntegrationPlatform.LINEAR)

        self.assertEqual(result.status, DispatchStatus.SUCCESS)
        self.assertTrue(result.external_task_id.startswith("LIN-"))
        self.assertIn("linear.app", result.external_task_url)

    def test_dispatch_to_asana_success(self):
        """Test dispatching to Asana REST API format."""
        result = self.dispatcher.dispatch_item(self.sample_item, IntegrationPlatform.ASANA)

        self.assertEqual(result.status, DispatchStatus.SUCCESS)
        self.assertIsNotNone(result.external_task_id)
        self.assertIn("asana.com", result.external_task_url)

    def test_dispatch_to_webhook_success(self):
        """Test dispatching to generic webhook listener."""
        result = self.dispatcher.dispatch_item(self.sample_item, IntegrationPlatform.WEBHOOK)

        self.assertEqual(result.status, DispatchStatus.SUCCESS)
        self.assertTrue(result.external_task_id.startswith("hook_"))

    def test_retry_and_dead_letter_queue_on_failure(self):
        """Test that repeated failures land in dead-letter queue after max retries."""
        result = self.dispatcher.dispatch_item(
            self.sample_item,
            IntegrationPlatform.JIRA,
            simulate_failure=True,
        )

        self.assertEqual(result.status, DispatchStatus.FAILED)
        self.assertEqual(result.retry_count, self.dispatcher.MAX_RETRIES)
        self.assertEqual(self.dispatcher.dead_letter_count, 1)

        # Retry dead letters should succeed
        reprocessed = self.dispatcher.retry_dead_letters()
        self.assertEqual(len(reprocessed), 1)
        self.assertEqual(reprocessed[0].status, DispatchStatus.SUCCESS)
        self.assertEqual(self.dispatcher.dead_letter_count, 0)

    def test_batch_dispatch(self):
        """Test dispatching multiple action items concurrently."""
        items = [
            ActionItemRecord(
                item_id=f"act_{i}",
                meeting_id="meet_standup",
                title=f"Task number {i}",
                description="Auto-generated task",
            )
            for i in range(5)
        ]

        results = self.dispatcher.dispatch_batch(items, IntegrationPlatform.WEBHOOK)
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.status == DispatchStatus.SUCCESS for r in results))

    def test_dispatch_history_serialization(self):
        """Test reading formatted dispatch history records."""
        self.dispatcher.dispatch_item(self.sample_item, IntegrationPlatform.JIRA)
        history = self.dispatcher.get_dispatch_history()

        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["platform"], "jira")
        self.assertEqual(history[0]["status"], "success")


if __name__ == "__main__":
    unittest.main()
