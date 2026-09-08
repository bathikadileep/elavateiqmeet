"""
ElevateIQ — Unit Tests for Google Congestion Controller (GCC)
==============================================================
Tests inter-arrival delay gradient estimation, dynamic threshold adaptation,
overuse/underuse detection, and AIMD packet-loss rate adjustments.
"""

import unittest
from backend.services.media.congestion_controller import (
    GoogleCongestionController,
    PacketFeedback,
    OveruseDetectorState,
    RateControlState
)


class TestGoogleCongestionController(unittest.TestCase):

    def setUp(self):
        self.gcc = GoogleCongestionController(peer_id="peer_gcc_101", initial_bitrate_kbps=2000)

    def test_initial_state(self):
        self.assertEqual(self.gcc.peer_id, "peer_gcc_101")
        self.assertEqual(self.gcc.target_bitrate_kbps, 2000.0)
        self.assertEqual(self.gcc.rate_state, RateControlState.INCREASE)
        self.assertEqual(self.gcc.detector_state, OveruseDetectorState.NORMAL)

    def test_additive_increase_on_clean_network(self):
        # 0% loss -> Additive increase
        new_rate = self.gcc.update_loss_feedback(packet_loss_fraction=0.0)
        self.assertGreater(new_rate, 2000.0)
        self.assertEqual(self.gcc.rate_state, RateControlState.INCREASE)

    def test_rate_hold_on_moderate_loss(self):
        # 5% loss -> Hold
        initial_rate = self.gcc.target_bitrate_kbps
        new_rate = self.gcc.update_loss_feedback(packet_loss_fraction=0.05)
        self.assertEqual(new_rate, initial_rate)
        self.assertEqual(self.gcc.rate_state, RateControlState.HOLD)

    def test_multiplicative_decrease_on_high_loss(self):
        # 15% loss -> Decrease
        initial_rate = self.gcc.target_bitrate_kbps
        new_rate = self.gcc.update_loss_feedback(packet_loss_fraction=0.15)
        self.assertLess(new_rate, initial_rate)
        self.assertEqual(self.gcc.rate_state, RateControlState.DECREASE)

    def test_delay_gradient_overuse_detection(self):
        # Packet 1 at t=0
        p1 = PacketFeedback(1, 1000.0, 1050.0, 1200)
        self.gcc.process_packet_feedback(p1)

        # Simulate consecutive packets arriving with increasing queuing delay (bufferbloat)
        # Send delta: 20ms, Recv delta: 120ms -> delay gradient = +100ms
        for seq in range(2, 8):
            p = PacketFeedback(seq, 1000.0 + (seq * 20.0), 1050.0 + (seq * 120.0), 1200)
            state = self.gcc.process_packet_feedback(p)

        self.assertEqual(state, OveruseDetectorState.OVERUSING)

        # High delay state must trigger rate decrease even if loss is 0%
        rate_after_overuse = self.gcc.update_loss_feedback(packet_loss_fraction=0.0)
        self.assertEqual(self.gcc.rate_state, RateControlState.DECREASE)

    def test_min_and_max_bitrate_bounds(self):
        # Repeated decrease should clamp to MIN_BITRATE_KBPS (100)
        for _ in range(50):
            self.gcc.update_loss_feedback(packet_loss_fraction=0.25)
        self.assertEqual(self.gcc.target_bitrate_kbps, self.gcc.MIN_BITRATE_KBPS)

        # Repeated increase should clamp to MAX_BITRATE_KBPS (20000)
        for _ in range(100):
            self.gcc.update_loss_feedback(packet_loss_fraction=0.0)
        self.assertEqual(self.gcc.target_bitrate_kbps, self.gcc.MAX_BITRATE_KBPS)


if __name__ == "__main__":
    unittest.main()
