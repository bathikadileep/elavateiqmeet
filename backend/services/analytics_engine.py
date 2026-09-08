"""
ElevateIQ — Enterprise Real-Time Analytics & QoE Insights Engine
===================================================================
Provides deep telemetry aggregation, audio/video quality metrics,
jitter buffer statistics, participant engagement scoring, and executive reporting.
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

log = logging.getLogger("elevateiq.services.analytics")


class AnalyticsEngine:
    """Enterprise Analytics Engine for telemetry aggregation and insights."""

    def __init__(self, sample_interval_seconds: int = 5):
        self.sample_interval = sample_interval_seconds
        self._telemetry_store: Dict[str, List[Dict[str, Any]]] = {}
        self._thresholds = {
            "max_jitter_ms": 50.0,
            "max_packet_loss_ratio": 0.05,
            "min_bitrate_kbps": 300.0,
            "target_framerate_fps": 30.0,
        }

    def ingest_telemetry_frame(self, meeting_code: str, participant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a raw telemetry snapshot frame from a WebRTC peer connection.
        Calculates instantaneous MOS (Mean Opinion Score) and updates store.
        """
        if meeting_code not in self._telemetry_store:
            self._telemetry_store[meeting_code] = []

        timestamp = payload.get("timestamp", datetime.now(timezone.utc).isoformat())
        bitrate_kbps = float(payload.get("bitrate_kbps", 0.0))
        packet_loss = float(payload.get("packet_loss_ratio", 0.0))
        jitter_ms = float(payload.get("jitter_ms", 0.0))
        fps = float(payload.get("framerate", 0.0))
        round_trip_time_ms = float(payload.get("rtt_ms", 0.0))

        # Calculate estimated MOS score (1.0 to 4.5 standard R-factor approximation)
        mos_score = self._compute_mos_score(bitrate_kbps, packet_loss, jitter_ms, round_trip_time_ms)

        frame = {
            "meeting_code": meeting_code,
            "participant_id": participant_id,
            "timestamp": timestamp,
            "bitrate_kbps": bitrate_kbps,
            "packet_loss_ratio": packet_loss,
            "jitter_ms": jitter_ms,
            "framerate": fps,
            "rtt_ms": round_trip_time_ms,
            "mos_score": mos_score,
            "network_quality": self._classify_quality(mos_score),
        }

        self._telemetry_store[meeting_code].append(frame)
        log.debug("Ingested telemetry frame for room %s user %s: MOS=%.2f", meeting_code, participant_id, mos_score)
        return frame

    def _compute_mos_score(self, bitrate_kbps: float, packet_loss: float, jitter_ms: float, rtt_ms: float) -> float:
        """
        Calculate ITU-T G.107 E-model R-factor approximation to estimate MOS.
        Returns float between 1.0 (unusable) and 4.5 (crystal clear).
        """
        effective_latency = rtt_ms + (jitter_ms * 2.0) + 10.0
        r_factor = 93.2 - (effective_latency / 40.0)

        if effective_latency > 160.0:
            r_factor -= (effective_latency - 160.0) / 10.0

        # Packet loss penalty
        r_factor -= packet_loss * 250.0

        # Bitrate boost/penalty
        if bitrate_kbps < 150.0:
            r_factor -= (150.0 - bitrate_kbps) / 5.0

        r_factor = max(0.0, min(100.0, r_factor))

        # Convert R-factor to MOS (1 - 4.5 scale)
        if r_factor < 0:
            return 1.0
        elif r_factor > 100:
            return 4.5
        else:
            mos = 1.0 + (0.035 * r_factor) + (r_factor * (r_factor - 60.0) * (100.0 - r_factor) * 0.000007)
            return round(max(1.0, min(4.5, mos)), 2)

    def _classify_quality(self, mos_score: float) -> str:
        """Classify network quality grade from MOS score."""
        if mos_score >= 4.1:
            return "EXCELLENT"
        elif mos_score >= 3.6:
            return "GOOD"
        elif mos_score >= 3.0:
            return "FAIR"
        elif mos_score >= 2.0:
            return "POOR"
        else:
            return "CRITICAL"

    def get_meeting_analytics_summary(self, meeting_code: str) -> Dict[str, Any]:
        """
        Retrieve aggregate meeting QoE analytics summary across all frames.
        """
        frames = self._telemetry_store.get(meeting_code, [])
        if not frames:
            return {
                "meeting_code": meeting_code,
                "total_frames": 0,
                "average_mos": 4.5,
                "average_bitrate_kbps": 0.0,
                "average_packet_loss": 0.0,
                "average_jitter_ms": 0.0,
                "quality_distribution": {"EXCELLENT": 0, "GOOD": 0, "FAIR": 0, "POOR": 0, "CRITICAL": 0},
                "health_index_pct": 100.0,
            }

        total_frames = len(frames)
        avg_mos = round(sum(f["mos_score"] for f in frames) / total_frames, 2)
        avg_bitrate = round(sum(f["bitrate_kbps"] for f in frames) / total_frames, 2)
        avg_loss = round(sum(f["packet_loss_ratio"] for f in frames) / total_frames, 4)
        avg_jitter = round(sum(f["jitter_ms"] for f in frames) / total_frames, 2)

        dist = {"EXCELLENT": 0, "GOOD": 0, "FAIR": 0, "POOR": 0, "CRITICAL": 0}
        for f in frames:
            grade = f["network_quality"]
            dist[grade] = dist.get(grade, 0) + 1

        good_frames = dist["EXCELLENT"] + dist["GOOD"]
        health_index = round((good_frames / total_frames) * 100.0, 2)

        return {
            "meeting_code": meeting_code,
            "total_frames": total_frames,
            "average_mos": avg_mos,
            "average_bitrate_kbps": avg_bitrate,
            "average_packet_loss": avg_loss,
            "average_jitter_ms": avg_jitter,
            "quality_distribution": dist,
            "health_index_pct": health_index,
        }

    def compute_engagement_score(self, audio_talk_time_sec: float, video_on_time_sec: float, chat_messages_sent: int, total_meeting_sec: float) -> Dict[str, Any]:
        """
        Compute participant engagement score (0 - 100%) based on participation metrics.
        """
        if total_meeting_sec <= 0:
            return {"engagement_score": 0.0, "tier": "INACTIVE"}

        video_ratio = min(1.0, video_on_time_sec / total_meeting_sec)
        talk_ratio = min(1.0, audio_talk_time_sec / (total_meeting_sec * 0.3))
        chat_boost = min(1.0, chat_messages_sent / 5.0)

        raw_score = (video_ratio * 40.0) + (talk_ratio * 40.0) + (chat_boost * 20.0)
        final_score = round(min(100.0, max(0.0, raw_score)), 1)

        tier = "HIGH" if final_score >= 70.0 else ("MEDIUM" if final_score >= 35.0 else "LOW")

        return {
            "engagement_score": final_score,
            "video_ratio_pct": round(video_ratio * 100, 1),
            "talk_ratio_pct": round(talk_ratio * 100, 1),
            "chat_messages": chat_messages_sent,
            "tier": tier,
        }

    def clear_meeting_data(self, meeting_code: str) -> bool:
        """Clear telemetry buffer for ended meeting."""
        if meeting_code in self._telemetry_store:
            del self._telemetry_store[meeting_code]
            return True
        return False
