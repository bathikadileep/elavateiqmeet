"""
ElevateIQ — Unit Tests for SIEM Syslog Streamer & Audit Log Vault
==================================================================
Tests ArcSight CEF string formatting, RFC 5424 Syslog generation,
event emission buffer, Merkle root computation, and cryptographic HMAC batch sealing.
"""

import unittest
from backend.services.enterprise.siem_syslog_streamer import (
    SiemSyslogStreamer,
    SiemSeverity,
    SiemAuditEvent,
    LogBatchSeal
)


class TestSiemSyslogStreamer(unittest.TestCase):

    def setUp(self):
        self.streamer = SiemSyslogStreamer(hmac_key="test-siem-key-999", max_batch_size=10)

    def test_format_to_cef(self):
        event = SiemAuditEvent(
            event_id="evt_test_001",
            tenant_id="tenant_stark_corp",
            event_class="AUTH_MFA_CHALLENGE_FAILED",
            event_name="MFA Passkey Verification Failure",
            severity=SiemSeverity.HIGH,
            actor_id="usr_tony_stark",
            actor_ip="194.22.10.5",
            room_code="room_war_room",
            details={"attempt_count": 3}
        )

        cef_str = self.streamer.format_to_cef(event)
        self.assertTrue(cef_str.startswith("CEF:0|ElevateIQ|MeetingPlatform|2.4.0|"))
        self.assertIn("AUTH_MFA_CHALLENGE_FAILED", cef_str)
        self.assertIn("MFA Passkey Verification Failure", cef_str)
        self.assertIn("|8|", cef_str)  # Severity HIGH = 8
        self.assertIn("actId=usr_tony_stark", cef_str)
        self.assertIn("src=194.22.10.5", cef_str)
        self.assertIn("cs1=room_war_room", cef_str)

    def test_format_to_rfc5424(self):
        event = SiemAuditEvent(
            event_id="evt_test_002",
            tenant_id="tenant_wayne",
            event_class="E2EE_KEY_ROTATION",
            event_name="MLS Group Epoch Advance",
            severity=SiemSeverity.MEDIUM,
            actor_id="usr_bruce",
            actor_ip="10.0.0.1"
        )

        rfc_str = self.streamer.format_to_rfc5424(event, hostname="sfu-node-01")
        self.assertTrue(rfc_str.startswith("<"))
        self.assertIn("sfu-node-01 elevateiq-audit 1 evt_test_002", rfc_str)
        self.assertIn('[audit@elevateiq tenant="tenant_wayne" actor="usr_bruce"', rfc_str)

    def test_emit_and_seal_batch(self):
        self.streamer.emit_event(
            tenant_id="t1",
            event_class="LOGIN_SUCCESS",
            event_name="User Login",
            severity=SiemSeverity.INFO,
            actor_id="u1",
            actor_ip="1.1.1.1"
        )
        self.streamer.emit_event(
            tenant_id="t1",
            event_class="MEETING_RECORDING_STARTED",
            event_name="Recording Started",
            severity=SiemSeverity.LOW,
            actor_id="u1",
            actor_ip="1.1.1.1",
            room_code="room_1"
        )

        self.assertEqual(len(self.streamer.buffer), 2)

        # Seal and flush
        result = self.streamer.seal_and_flush_batch()
        self.assertIsNotNone(result)
        seal, cef_lines = result

        self.assertEqual(seal.event_count, 2)
        self.assertEqual(len(seal.merkle_root), 64)
        self.assertEqual(len(seal.hmac_signature), 64)
        self.assertEqual(len(cef_lines), 2)
        self.assertEqual(len(self.streamer.buffer), 0)
        self.assertEqual(len(self.streamer.archived_batches), 1)

    def test_flush_empty_buffer_returns_none(self):
        res = self.streamer.seal_and_flush_batch()
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
