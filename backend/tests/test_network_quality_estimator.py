"""
ElevateIQ — Unit Tests for WebRTC Network Quality Estimator
============================================================
Tests Kalman filter RTT smoothing, G.107 E-model MOS scoring, congestion state classification,
adaptive video layer preset recommendations, and FEC redundancy triggers.
"""

import unittest
from backend.services.telemetry.network_quality_estimator import (
    NetworkQualityEstimator,
    CongestionState,
    VideoLayerPreset
)


class TestNetworkQualityEstimator(unittest.TestCase):

    def setUp(self):
        self.prober = NetworkQualityEstimator(peer_id="peer_webrtc_99", room_code="room-tele-505")

    def test_initial_state(self):
        self.assertEqual(self.prober.peer_id, "peer_webrtc_99")
        self.assertEqual(self.prober.room_code, "room-tele-505")
        self.assertEqual(self.prober.estimated_rtt_ms, 60.0)

    def test_kalman_rtt_filter_smoothing(self):
        # Initial estimate is 60ms. Feed a noisy spike of 200ms
        res1 = self.prober.update_telemetry(measured_rtt_ms=200.0, jitter_ms=5.0, packet_loss_pct=0.0)
        # Smoothed RTT should increase gradually rather than jumping straight to 200ms
        self.assertGreater(res1["smoothed_rtt_ms"], 60.0)
        self.assertLess(res1["smoothed_rtt_ms"], 200.0)

        # Consistent low RTT inputs should converge
        for _ in range(5):
            self.prober.update_telemetry(measured_rtt_ms=30.0, jitter_ms=2.0, packet_loss_pct=0.0)
        self.assertLess(self.prober.estimated_rtt_ms, 50.0)

    def test_mos_calculation_clean_network(self):
        # Clean fiber connection: 20ms RTT, 2ms jitter, 0% loss
        self.prober.estimated_rtt_ms = 20.0
        self.prober.last_jitter_ms = 2.0
        self.prober.last_packet_loss_pct = 0.0

        mos = self.prober.calculate_mos()
        # Should be excellent (> 4.2)
        self.assertGreater(mos, 4.2)
        self.assertLessEqual(mos, 4.5)

    def test_mos_calculation_degraded_network(self):
        # Degraded connection: 400ms RTT, 30ms jitter, 10% packet loss
        self.prober.estimated_rtt_ms = 400.0
        self.prober.last_jitter_ms = 30.0
        self.prober.last_packet_loss_pct = 10.0

        mos = self.prober.calculate_mos()
        # Should be noticeably degraded (< 3.0)
        self.assertLess(mos, 3.0)
        self.assertGreaterEqual(mos, 1.0)

    def test_congestion_classification_tiers(self):
        # Excellent
        self.prober.estimated_rtt_ms = 30.0
        self.prober.last_jitter_ms = 3.0
        self.prober.last_packet_loss_pct = 0.0
        self.assertEqual(self.prober.classify_congestion(), CongestionState.EXCELLENT)

        # Constrained
        self.prober.estimated_rtt_ms = 280.0
        self.prober.last_jitter_ms = 20.0
        self.prober.last_packet_loss_pct = 5.0
        self.assertEqual(self.prober.classify_congestion(), CongestionState.CONSTRAINED)

        # Critical
        self.prober.estimated_rtt_ms = 600.0
        self.prober.last_packet_loss_pct = 20.0
        self.assertEqual(self.prober.classify_congestion(), CongestionState.CRITICAL)

    def test_adaptive_video_preset_recommendation(self):
        # High bandwidth (6000 kbps, low latency) -> 4K or 1080P
        self.prober.estimated_bandwidth_kbps = 6500.0
        self.prober.estimated_rtt_ms = 25.0
        self.prober.last_packet_loss_pct = 0.0
        preset_high = self.prober.recommend_video_preset()
        self.assertIn(preset_high.profile_name, ("4K_UHD", "FHD_1080P"))

        # Low bandwidth (300 kbps) -> 360P
        self.prober.estimated_bandwidth_kbps = 350.0
        self.prober.estimated_rtt_ms = 180.0
        self.prober.last_packet_loss_pct = 4.0
        preset_low = self.prober.recommend_video_preset()
        self.assertEqual(preset_low.profile_name, "SD_360P")

        # Critical congestion -> Audio Only fallback
        self.prober.estimated_bandwidth_kbps = 80.0
        self.prober.estimated_rtt_ms = 700.0
        self.prober.last_packet_loss_pct = 25.0
        preset_critical = self.prober.recommend_video_preset()
        self.assertTrue(preset_critical.audio_only)

    def test_fec_boost_triggers(self):
        # Normal (0% loss) -> No FEC
        self.prober.last_packet_loss_pct = 0.5
        boost, overhead = self.prober.should_trigger_fec_boost()
        self.assertFalse(boost)
        self.assertEqual(overhead, 0)

        # Moderate loss (5%) -> 20% FEC
        self.prober.last_packet_loss_pct = 5.0
        boost, overhead = self.prober.should_trigger_fec_boost()
        self.assertTrue(boost)
        self.assertEqual(overhead, 20)

        # Severe loss (12%) -> 40% FEC
        self.prober.last_packet_loss_pct = 12.0
        boost, overhead = self.prober.should_trigger_fec_boost()
        self.assertTrue(boost)
        self.assertEqual(overhead, 40)


if __name__ == "__main__":
    unittest.main()
