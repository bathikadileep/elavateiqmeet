"""
ElevateIQ — Unit & Integration Test Suite for Analytics & QoE Insights Engine
================================================================================
Comprehensive assertions for MOS calculation, telemetry frame ingestion,
engagement scoring, quality classification, and room summary aggregation.
"""

import unittest
from datetime import datetime, timezone
from backend.services.analytics_engine import AnalyticsEngine


class AnalyticsEngineTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = AnalyticsEngine(sample_interval_seconds=5)

    def test_telemetry_frame_ingestion_and_mos_calculation(self):
        """Test ingesting WebRTC telemetry frame and computing MOS score."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bitrate_kbps": 2500.0,
            "packet_loss_ratio": 0.001,
            "jitter_ms": 5.0,
            "framerate": 30.0,
            "rtt_ms": 20.0,
        }

        frame = self.engine.ingest_telemetry_frame("room-101-analytics", "user-peer-1", payload)
        self.assertEqual(frame["meeting_code"], "room-101-analytics")
        self.assertGreaterEqual(frame["mos_score"], 4.0)
        self.assertEqual(frame["network_quality"], "EXCELLENT")

    def test_poor_network_classification(self):
        """Test degrading network metrics result in POOR or CRITICAL MOS grade."""
        payload = {
            "bitrate_kbps": 100.0,
            "packet_loss_ratio": 0.15,
            "jitter_ms": 120.0,
            "framerate": 10.0,
            "rtt_ms": 350.0,
        }

        frame = self.engine.ingest_telemetry_frame("room-poor-net", "user-peer-2", payload)
        self.assertLess(frame["mos_score"], 3.0)
        self.assertIn(frame["network_quality"], ["POOR", "CRITICAL"])

    def test_meeting_analytics_summary_aggregation(self):
        """Test aggregating meeting telemetry frames across multiple samples."""
        code = "room-summary-test"
        for i in range(10):
            self.engine.ingest_telemetry_frame(code, f"user-{i % 3}", {
                "bitrate_kbps": 2000.0 + (i * 50),
                "packet_loss_ratio": 0.002,
                "jitter_ms": 10.0,
                "rtt_ms": 30.0,
            })

        summary = self.engine.get_meeting_analytics_summary(code)
        self.assertEqual(summary["total_frames"], 10)
        self.assertGreater(summary["average_mos"], 3.5)
        self.assertEqual(summary["health_index_pct"], 100.0)

    def test_engagement_score_computation(self):
        """Test computing engagement score tiers for active vs passive users."""
        active_res = self.engine.compute_engagement_score(
            audio_talk_time_sec=120.0,
            video_on_time_sec=300.0,
            chat_messages_sent=4,
            total_meeting_sec=300.0
        )
        self.assertEqual(active_res["tier"], "HIGH")
        self.assertGreaterEqual(active_res["engagement_score"], 70.0)

        passive_res = self.engine.compute_engagement_score(
            audio_talk_time_sec=0.0,
            video_on_time_sec=0.0,
            chat_messages_sent=0,
            total_meeting_sec=300.0
        )
        self.assertEqual(passive_res["tier"], "LOW")
        self.assertEqual(passive_res["engagement_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
