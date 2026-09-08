"""
ElevateIQ — WebRTC SFU Simulcast Layer Switching Integration Test Suite
========================================================================
Tests SFU dynamic layer switching across Low, Medium, High, and Full HD simulcast streams.
"""

import unittest
from backend.services.adaptive_bitrate_engine import AdaptiveBitrateEngine


class SFUSimulcastLayerSwitchTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = AdaptiveBitrateEngine()

    def test_simulcast_layer_adaptation_pipeline(self):
        """Test peer bandwidth estimate update triggers spatial layer transition."""
        self.engine.register_peer("peer_sfu_1", 2000.0)

        # 1. Adapt to low
        s1 = self.engine.update_bandwidth_estimate("peer_sfu_1", 150.0, 0.15)
        self.assertEqual(s1["active_layer"], "low")

        # 2. Adapt to high
        s2 = self.engine.update_bandwidth_estimate("peer_sfu_1", 2200.0, 0.01)
        self.assertEqual(s2["active_layer"], "high")


if __name__ == "__main__":
    unittest.main()
