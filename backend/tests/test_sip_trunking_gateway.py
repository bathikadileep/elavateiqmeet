"""
ElevateIQ — Unit Test Suite for SIP Trunking Gateway
=====================================================
Tests RFC 3261 INVITE handling, SDP parsing, DTMF PIN collection,
RTP telemetry updates, and call teardown.
"""

import unittest
from backend.services.media.sip_trunking_gateway import (
    SIPTrunkingGateway,
    SIPCallState,
    AudioCodec,
    SDPDescriptor,
)


class SIPTrunkingGatewayTestSuite(unittest.TestCase):

    def setUp(self):
        self.gateway = SIPTrunkingGateway(bind_ip="10.0.0.1", sip_port=5060)
        self.meeting_id = "meet_alpha_789"
        self.pin = self.gateway.register_meeting_dialin_pin(self.meeting_id, "849201")

    def test_pin_registration_and_lookup(self):
        """Verify meeting dial-in PIN resolution."""
        self.assertEqual(self.gateway.get_meeting_for_pin("849201"), self.meeting_id)
        self.assertEqual(self.gateway.get_meeting_for_pin("849201#"), self.meeting_id)
        self.assertIsNone(self.gateway.get_meeting_for_pin("999999"))

    def test_sdp_serialize_and_parse(self):
        """Test SDP offer serialization and round-trip parsing."""
        sdp = SDPDescriptor(
            session_id="123456789",
            session_version=1,
            originator="caller-gw",
            connection_ip="192.168.1.100",
            audio_port=18000,
            supported_codecs=[AudioCodec.OPUS, AudioCodec.PCMU, AudioCodec.TELEPHONE_EVENT],
            crypto_key_base64="dGVzdF9rZXlfYnl0ZXNfZm9yX3NydHA=",
        )
        serialized = sdp.serialize()
        self.assertIn("v=0", serialized)
        self.assertIn("c=IN IP4 192.168.1.100", serialized)
        self.assertIn("m=audio 18000 RTP/SAVP", serialized)
        self.assertIn("a=crypto:1", serialized)

        parsed = SDPDescriptor.parse(serialized)
        self.assertEqual(parsed.connection_ip, "192.168.1.100")
        self.assertEqual(parsed.audio_port, 18000)

    def test_inbound_invite_accepted(self):
        """Test processing of inbound SIP INVITE request."""
        sample_sdp = (
            "v=0\r\n"
            "o=caller 100 1 IN IP4 203.0.113.10\r\n"
            "s=SIP Call\r\n"
            "c=IN IP4 203.0.113.10\r\n"
            "t=0 0\r\n"
            "m=audio 16400 RTP/AVP 0 101\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
            "a=rtpmap:101 telephone-event/8000\r\n"
        )
        code, reason, resp_sdp = self.gateway.handle_inbound_invite(
            call_id="call-uuid-101",
            from_uri="sip:+14155552671@pstn.carrier.net",
            to_uri="sip:bridge@meet.elevateiq.com",
            remote_ip="203.0.113.10",
            raw_sdp=sample_sdp
        )

        self.assertEqual(code, 200)
        self.assertEqual(reason, "OK")
        self.assertIsNotNone(resp_sdp)
        self.assertIn("m=audio", resp_sdp)

        # Call should now be in active list
        active = self.gateway.get_active_calls_summary()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["call_id"], "call-uuid-101")
        self.assertEqual(active[0]["caller_id"], "+14155552671")
        self.assertEqual(active[0]["state"], SIPCallState.CONNECTED.value)

    def test_dtmf_pin_entry_flow(self):
        """Test collecting digits and authenticating into room."""
        # Setup active call
        self.gateway.handle_inbound_invite(
            call_id="call-uuid-102",
            from_uri="sip:+14155559999@carrier.net",
            to_uri="sip:bridge@elevateiq.com",
            remote_ip="203.0.113.10",
            raw_sdp=""
        )

        # Digits: 8 -> 4 -> 9 -> 2 -> 0 -> 1 -> #
        for d in "84920":
            res = self.gateway.handle_dtmf_digit("call-uuid-102", d)
            self.assertEqual(res["status"], "COLLECTING")

        res_final = self.gateway.handle_dtmf_digit("call-uuid-102", "1")
        self.assertEqual(res_final["status"], "COLLECTING")

        # Submit with pound key '#'
        res_auth = self.gateway.handle_dtmf_digit("call-uuid-102", "#")
        self.assertEqual(res_auth["status"], "AUTHENTICATED")
        self.assertEqual(res_auth["meeting_id"], self.meeting_id)

        # Active call should now show authenticated
        summary = self.gateway.get_active_calls_summary()[0]
        self.assertTrue(summary["is_authenticated"])
        self.assertEqual(summary["meeting_id"], self.meeting_id)

    def test_dtmf_invalid_pin_rejected(self):
        """Test wrong PIN rejection."""
        self.gateway.handle_inbound_invite("call-uuid-103", "sip:caller@net", "sip:gw@net", "10.0.0.1", "")
        for d in "000000#":
            res = self.gateway.handle_dtmf_digit("call-uuid-103", d)

        self.assertEqual(res["status"], "INVALID_PIN")
        self.assertEqual(res["entered_code"], "000000")

    def test_call_termination_bye(self):
        """Test SIP BYE hangup."""
        self.gateway.handle_inbound_invite("call-uuid-104", "sip:caller@net", "sip:gw@net", "10.0.0.1", "")
        code, reason = self.gateway.handle_inbound_bye("call-uuid-104")
        self.assertEqual(code, 200)
        self.assertEqual(len(self.gateway.get_active_calls_summary()), 0)

    def test_server_initiated_termination(self):
        """Test server disconnect."""
        self.gateway.handle_inbound_invite("call-uuid-105", "sip:caller@net", "sip:gw@net", "10.0.0.1", "")
        terminated = self.gateway.terminate_call("call-uuid-105", reason="Room closed")
        self.assertTrue(terminated)
        self.assertEqual(len(self.gateway.get_active_calls_summary()), 0)

    def test_rtp_telemetry_recording(self):
        """Test updating jitter and packet loss metrics."""
        self.gateway.handle_inbound_invite("call-uuid-106", "sip:caller@net", "sip:gw@net", "10.0.0.1", "")
        self.gateway.record_rtp_telemetry("call-uuid-106", rx_packets=500, tx_packets=490, lost=3, jitter_ms=12.4)

        summary = self.gateway.get_active_calls_summary()[0]
        self.assertEqual(summary["packets_rx"], 500)
        self.assertEqual(summary["packets_lost"], 3)
        self.assertEqual(summary["jitter_ms"], 12.4)


if __name__ == "__main__":
    unittest.main()
