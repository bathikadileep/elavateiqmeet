"""
ElevateIQ — WebRTC QoE Telemetry & Network Health Analytics
============================================================
Collects client-side WebRTC `getStats()` metrics (round-trip time RTT, jitter, packet loss percentage,
audio level, video frame resolution, and bitrate) to compute Quality of Experience (QoE) scores.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.telemetry")


class TelemetryService:
    """WebRTC Network Telemetry & MOS (Mean Opinion Score) Evaluator."""

    @staticmethod
    def evaluate_qoe_score(rtt_ms: float, packet_loss_pct: float, jitter_ms: float) -> Dict[str, Any]:
        """
        Calculate ITU-T R-factor and estimated MOS (Mean Opinion Score, scale 1.0 to 4.5)
        for WebRTC audio/video stream quality assessment.
        """
        # Effective Latency calculation
        effective_latency = rtt_ms + (jitter_ms * 2) + 10.0

        # R-Factor calculation (simplified E-model)
        if effective_latency < 160.0:
            r_factor = 93.2 - (effective_latency / 40.0)
        else:
            r_factor = 93.2 - ((effective_latency - 120.0) / 10.0)

        # Subtract packet loss penalty
        r_factor -= (packet_loss_pct * 2.5)
        r_factor = max(0.0, min(100.0, r_factor))

        # Convert R-factor to MOS (1.0 to 4.5)
        if r_factor < 60.0:
            mos = 1.0 + (0.035 * r_factor) + (0.000007 * r_factor * (r_factor - 60.0) * (100.0 - r_factor))
        else:
            mos = 1.0 + (0.035 * r_factor) + (0.000007 * r_factor * (r_factor - 60.0) * (100.0 - r_factor))

        mos = round(max(1.0, min(4.5, mos)), 2)

        # Rating label
        if mos >= 4.0:
            quality = "excellent"
        elif mos >= 3.5:
            quality = "good"
        elif mos >= 3.0:
            quality = "fair"
        elif mos >= 2.5:
            quality = "poor"
        else:
            quality = "bad"

        return {
            "mos_score": mos,
            "quality_rating": quality,
            "effective_latency_ms": round(effective_latency, 1),
            "rtt_ms": rtt_ms,
            "packet_loss_pct": packet_loss_pct,
            "jitter_ms": jitter_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def process_client_telemetry_report(room_code: str, user_id: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest raw getStats() report from client browser."""
        rtt = float(stats.get("rtt_ms", 50.0))
        loss = float(stats.get("packet_loss_pct", 0.5))
        jitter = float(stats.get("jitter_ms", 5.0))

        qoe_eval = TelemetryService.evaluate_qoe_score(rtt, loss, jitter)
        qoe_eval["room_code"] = room_code
        qoe_eval["user_id"] = user_id

        if qoe_eval["quality_rating"] in ["poor", "bad"]:
            log.warning("Low QoE network alert in room %s for user %s (MOS: %.2f)", room_code, user_id, qoe_eval["mos_score"])

        return qoe_eval
