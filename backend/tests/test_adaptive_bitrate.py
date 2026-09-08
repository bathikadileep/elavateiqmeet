"""
ElevateIQ — Unit Test Suite for WebRTC Adaptive Bitrate Engine
===============================================================
Tests peer registration, Simulcast layer switching, and GCC congestion feedback.
"""

import unittest
from backend.services.adaptive_bitrate_engine import AdaptiveBitrateEngine


class AdaptiveBitrateTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = AdaptiveBitrateEngine()

    def test_peer_registration_and_initial_state(self):
        """Test initial peer registration with default high layer."""
        state = self.engine.register_peer("peer_001", initial_bandwidth_kbps=2500.0)
        self.assertEqual(state["peer_id"], "peer_001")
        self.assertEqual(state["active_layer"], "high")
        self.assertEqual(state["congestion_state"], "NORMAL")

    def test_heavy_congestion_downscaling(self):
        """Test downscaling to low layer under heavy packet loss and low bandwidth."""
        state = self.engine.update_bandwidth_estimate("peer_001", new_estimated_kbps=180.0, packet_loss_pct=0.12)
        self.assertEqual(state["active_layer"], "low")
        self.assertEqual(state["congestion_state"], "HEAVY_CONGESTION")
        self.assertEqual(state["target_resolution"], "320x180")

    def test_optimal_bandwidth_upscaling(self):
        """Test upscaling to full HD layer under high bandwidth."""
        state = self.engine.update_bandwidth_estimate("peer_002", new_estimated_kbps=4000.0, packet_loss_pct=0.001)
        self.assertEqual(state["active_layer"], "full_hd")
        self.assertEqual(state["target_resolution"], "1920x1080")

    def test_aggregate_sfu_stream_config(self):
        """Test computing total SFU egress load across multiple peers."""
        self.engine.register_peer("p1", 4000.0)
        self.engine.register_peer("p2", 200.0)
        self.engine.update_bandwidth_estimate("p2", 200.0, 0.15)

        config = self.engine.calculate_active_stream_config(["p1", "p2"])
        self.assertEqual(config["active_peers_count"], 2)
        self.assertIn("full_hd", config["layer_distribution"])
        self.assertIn("low", config["layer_distribution"])


if __name__ == "__main__":
    unittest.main()
