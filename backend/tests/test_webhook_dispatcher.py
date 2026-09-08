"""
ElevateIQ — Unit Tests for Outbound Webhook Dispatcher
=======================================================
Tests HMAC-SHA256 signature generation, replay attack prevention, event dispatching,
retry logic, dead-letter queue (DLQ) ingestion, and circuit breaker trip dynamics.
"""

import time
import unittest
from backend.services.enterprise.webhook_dispatcher import (
    WebhookDispatcher,
    WebhookEventType,
    WebhookSubscription,
    CircuitState
)


class TestWebhookDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = WebhookDispatcher()
        self.sub = self.dispatcher.register_subscription(
            subscription_id="sub_slack_alerts",
            tenant_id="org_acme",
            target_url="https://hooks.slack.com/services/T00/B00/X00",
            secret_key="whsec_test_secret_123",
            events=[WebhookEventType.MEETING_STARTED, WebhookEventType.RECORDING_READY]
        )

    def test_signature_generation_and_verification(self):
        payload = b'{"event":"meeting.started","room_code":"room_101"}'
        ts = int(time.time())
        sig = self.dispatcher.generate_signature(payload, "whsec_test_secret_123", ts)

        # Must verify True
        is_valid = self.dispatcher.verify_signature(sig, payload, "whsec_test_secret_123")
        self.assertTrue(is_valid)

        # Corrupted payload must verify False
        corrupted = b'{"event":"meeting.started","room_code":"room_HACKED"}'
        self.assertFalse(self.dispatcher.verify_signature(sig, corrupted, "whsec_test_secret_123"))

        # Wrong secret must verify False
        self.assertFalse(self.dispatcher.verify_signature(sig, payload, "whsec_wrong_key"))

    def test_replay_attack_prevention(self):
        payload = b'{"event":"meeting.started"}'
        old_ts = int(time.time()) - 600  # 10 minutes in the past
        old_sig = self.dispatcher.generate_signature(payload, "whsec_test_secret_123", old_ts)

        # Should fail due to tolerance window (default 300s)
        self.assertFalse(self.dispatcher.verify_signature(old_sig, payload, "whsec_test_secret_123", tolerance_sec=300))

    def test_dispatch_event_success(self):
        def mock_success(url, payload_json, headers, attempt):
            return 200, None

        attempts = self.dispatcher.dispatch_event(
            event_type=WebhookEventType.MEETING_STARTED,
            payload={"room_code": "room_alpha"},
            tenant_id="org_acme",
            mock_sender=mock_success
        )

        self.assertEqual(len(attempts), 1)
        self.assertTrue(attempts[0].is_success)
        self.assertEqual(attempts[0].http_status, 200)
        self.assertEqual(len(self.dispatcher.dead_letter_queue), 0)

    def test_dispatch_retry_and_dlq_on_failure(self):
        def mock_failing(url, payload_json, headers, attempt):
            return 500, "Internal Server Error on remote endpoint"

        attempts = self.dispatcher.dispatch_event(
            event_type=WebhookEventType.MEETING_STARTED,
            payload={"room_code": "room_beta"},
            tenant_id="org_acme",
            mock_sender=mock_failing
        )

        # Should attempt 3 times (MAX_RETRIES)
        self.assertEqual(len(attempts), 3)
        self.assertFalse(attempts[-1].is_success)

        # Should be deposited into DLQ
        self.assertEqual(len(self.dispatcher.dead_letter_queue), 1)
        dlq_item = self.dispatcher.dead_letter_queue[0]
        self.assertEqual(dlq_item["subscription_id"], "sub_slack_alerts")
        self.assertEqual(dlq_item["event_type"], WebhookEventType.MEETING_STARTED.value)

    def test_circuit_breaker_trips_to_open(self):
        def mock_error(url, payload_json, headers, attempt):
            return 503, "Service Unavailable"

        # Trigger failures up to threshold
        for _ in range(2):
            self.dispatcher.dispatch_event(
                event_type=WebhookEventType.MEETING_STARTED,
                payload={"room": "test"},
                tenant_id="org_acme",
                mock_sender=mock_error
            )

        # After 6 failures (> threshold 5), circuit should be OPEN
        self.assertEqual(self.sub.circuit_state, CircuitState.OPEN)

        # Subsequent dispatch should be fast-failed/dropped without sending
        new_attempts = self.dispatcher.dispatch_event(
            event_type=WebhookEventType.MEETING_STARTED,
            payload={"room": "test"},
            tenant_id="org_acme",
            mock_sender=mock_error
        )
        self.assertEqual(len(new_attempts), 0)


if __name__ == "__main__":
    unittest.main()
