"""
ElevateIQ — Unit Test Suite for Google Congestion Control (GCC) Telemetry Feedback
===================================================================================
Tests WebRTC TWCC/GCC bandwidth adaptation transitions under lossy network conditions.
"""

import unittest
from backend.services.adaptive_bitrate_engine import AdaptiveBitrateEngine


class AdaptiveBitrateGCCTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = AdaptiveBitrateEngine()

    def test_gcc_bandwidth_adaptation_curve(self):
        """Test transitioning peer across multiple simulcast layers as bandwidth fluctuates."""
        self.engine.register_peer("peer_gcc_101", 3000.0)

        # 1. Normal state -> High layer
        s1 = self.engine.update_bandwidth_estimate("peer_gcc_101", 2000.0, 0.01)
        self.assertEqual(s1["active_layer"], "high")

        # 2. Network drop -> Moderate congestion -> Medium layer
        s2 = self.engine.update_bandwidth_estimate("peer_gcc_101", 600.0, 0.05)
        self.assertEqual(s2["active_layer"], "medium")

        # 3. Recovery -> Full HD layer
        s3 = self.engine.update_bandwidth_estimate("peer_gcc_101", 4000.0, 0.001)
        self.assertEqual(s3["active_layer"], "full_hd")


if __name__ == "__main__":
    unittest.main()
