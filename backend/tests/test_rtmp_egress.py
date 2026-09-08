"""
ElevateIQ — Unit Test Suite for Live Broadcast RTMP Egress Engine
===================================================================
Tests initializing RTMP streaming sessions to YouTube Live / Twitch / LinkedIn Live and stream state lifecycle.
"""

import unittest
from backend.services.rtmp_egress import RTMPEgressService


class RTMPEgressTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = RTMPEgressService()

    def test_start_rtmp_broadcast_session(self):
        """Test starting live RTMP egress broadcast stream to external endpoint."""
        session = self.service.start_rtmp_stream(
            room_code="room-rtmp-101",
            rtmp_url="rtmp://a.rtmp.youtube.com/live2",
            stream_key="live_123456789_key"
        )

        self.assertEqual(session["room_code"], "room-rtmp-101")
        self.assertEqual(session["status"], "streaming")
        self.assertIn("youtube.com", session["rtmp_endpoint"])

    def test_stop_rtmp_broadcast_session(self):
        """Test terminating active RTMP egress stream."""
        self.service.start_rtmp_stream("room-rtmp-101", "rtmp://twitch.tv/app", "key_abc")
        stopped = self.service.stop_rtmp_stream("room-rtmp-101")

        self.assertEqual(stopped["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
