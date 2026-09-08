"""
Tests for WebRTC Adaptive Bitrate (ABR) Video Layer Selector & CPU Health Throttler
==================================================================================
Validates bandwidth scoring, CPU load throttling, spatial/temporal switching,
and hysteresis dwell delay enforcement.
"""

import time
import unittest
from backend.services.media.abr_layer_selector import (
    AbrLayerSelector,
    ClientMetricsReport,
    SpatialLayer,
    TemporalLayer,
    CpuPressureLevel,
)


class TestAbrLayerSelector(unittest.TestCase):

    def setUp(self):
        self.selector = AbrLayerSelector()
        self.peer_id = "peer_test_abr_1"
        self.selector.register_peer(self.peer_id, initial_spatial=SpatialLayer.HD_720P)

    def test_nominal_high_bandwidth_upgrade(self):
        now = time.time()
        # High bandwidth report (3500 kbps, 0% loss, 25% CPU)
        report = ClientMetricsReport(
            peer_id=self.peer_id,
            available_bandwidth_kbps=3500,
            round_trip_time_ms=30.0,
            packet_loss_ratio=0.01,
            jitter_ms=5.0,
            cpu_usage_pct=25.0,
            dropped_frames_pct=0.0,
            timestamp=now,
        )

        # 1st evaluation -> hysteresis waiting
        dec1 = self.selector.evaluate_metrics(report)
        self.assertEqual(dec1.spatial, SpatialLayer.HD_720P)  # Stays at 720p initially

        # Dwell time expires (advance clock by 6 seconds)
        report2 = ClientMetricsReport(
            peer_id=self.peer_id,
            available_bandwidth_kbps=3500,
            round_trip_time_ms=30.0,
            packet_loss_ratio=0.01,
            jitter_ms=5.0,
            cpu_usage_pct=25.0,
            dropped_frames_pct=0.0,
            timestamp=now + 6.0,
        )
        dec2 = self.selector.evaluate_metrics(report2)
        self.assertEqual(dec2.spatial, SpatialLayer.FHD_1080P)
        self.assertEqual(dec2.temporal, TemporalLayer.FPS_60)
        self.assertTrue(dec2.transitioned)

    def test_critical_cpu_pressure_downgrades(self):
        now = time.time()
        # Even with high bandwidth (5000 kbps), 92% CPU triggers critical throttling
        report = ClientMetricsReport(
            peer_id=self.peer_id,
            available_bandwidth_kbps=5000,
            round_trip_time_ms=40.0,
            packet_loss_ratio=0.0,
            jitter_ms=2.0,
            cpu_usage_pct=92.0,
            dropped_frames_pct=28.0,
            timestamp=now,
        )
        self.selector.evaluate_metrics(report)

        # Fast downgrade after 1.5s
        report2 = ClientMetricsReport(
            peer_id=self.peer_id,
            available_bandwidth_kbps=5000,
            round_trip_time_ms=40.0,
            packet_loss_ratio=0.0,
            jitter_ms=2.0,
            cpu_usage_pct=92.0,
            dropped_frames_pct=28.0,
            timestamp=now + 1.5,
        )
        dec = self.selector.evaluate_metrics(report2)
        self.assertEqual(dec.spatial, SpatialLayer.LD_180P)
        self.assertEqual(dec.cpu_pressure, CpuPressureLevel.CRITICAL)

    def test_severe_packet_loss_audio_fallback(self):
        now = time.time()
        # 35% packet loss
        report = ClientMetricsReport(
            peer_id=self.peer_id,
            available_bandwidth_kbps=800,
            round_trip_time_ms=180.0,
            packet_loss_ratio=0.35,
            jitter_ms=65.0,
            cpu_usage_pct=30.0,
            dropped_frames_pct=5.0,
            timestamp=now + 2.0,
        )
        dec = self.selector.evaluate_metrics(report)
        self.assertEqual(dec.spatial, SpatialLayer.DISABLED)
        self.assertIn("audio-only fallback", dec.reason)

    def test_moderate_cpu_caps_at_720p(self):
        now = time.time()
        # 80% CPU with huge bandwidth -> should cap at 720p
        report = ClientMetricsReport(
            peer_id=self.peer_id,
            available_bandwidth_kbps=8000,
            round_trip_time_ms=20.0,
            packet_loss_ratio=0.0,
            jitter_ms=1.0,
            cpu_usage_pct=80.0,
            dropped_frames_pct=11.0,
            timestamp=now + 6.0,
        )
        dec = self.selector.evaluate_metrics(report)
        self.assertEqual(dec.spatial, SpatialLayer.HD_720P)
        self.assertEqual(dec.cpu_pressure, CpuPressureLevel.MODERATE)


if __name__ == "__main__":
    unittest.main()
