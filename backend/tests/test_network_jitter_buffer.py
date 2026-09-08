"""
ElevateIQ — Unit Test Suite for WebRTC NetEQ Jitter Buffer Controller
======================================================================
Tests computing NetEQ playout target delay.
"""

import unittest
from backend.services.telemetry.network_jitter_buffer import NetworkJitterBufferController


class NetworkJitterBufferTestSuite(unittest.TestCase):

    def setUp(self):
        self.controller = NetworkJitterBufferController()

    def test_compute_target_delay(self):
        """Test NetEQ target delay calculation under jitter and packet loss."""
        delay = self.controller.compute_target_delay_ms(current_jitter_ms=10.0, packet_loss_ratio=0.01)
        self.assertGreaterEqual(delay, 20.0)
        self.assertLessEqual(delay, 250.0)


if __name__ == "__main__":
    unittest.main()
