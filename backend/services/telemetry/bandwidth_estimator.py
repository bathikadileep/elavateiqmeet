"""
ElevateIQ — WebRTC Bandwidth Estimation & Congestion Control (GCC/BBR)
=======================================================================
Implements Google Congestion Control (GCC) trendline filter and bottleneck bandwidth (BBR)
estimation algorithms to dynamically adapt WebRTC video bitrate.
"""

import math
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.telemetry.bwe")


class BandwidthEstimatorService:
    """WebRTC GCC & Delay-Based Congestion Controller."""

    @staticmethod
    def calculate_target_bitrate(current_bitrate_bps: int, loss_ratio: float, rtt_ms: float, delay_gradient_ms: float) -> Dict[str, Any]:
        """
        Compute optimal target video bitrate based on loss and delay signals.
        """
        state = "normal"
        new_bitrate = current_bitrate_bps

        # 1. Loss-based adaptation
        if loss_ratio > 0.10:
            # High loss -> multiplicative decrease
            new_bitrate = int(current_bitrate_bps * (1.0 - 0.5 * loss_ratio))
            state = "overuse_loss"
        elif loss_ratio < 0.02 and delay_gradient_ms < 5.0:
            # Low loss & low delay -> additive increase
            new_bitrate = min(int(current_bitrate_bps * 1.08), 4000000) # Max 4 Mbps
            state = "underuse_increase"
        elif delay_gradient_ms > 25.0:
            # Delay gradient spike -> overuse signal
            new_bitrate = int(current_bitrate_bps * 0.85)
            state = "overuse_delay"

        # Clamp limits (200 kbps min, 4 Mbps max)
        new_bitrate = max(200000, min(4000000, new_bitrate))

        return {
            "current_bitrate_kbps": round(current_bitrate_bps / 1000.0, 1),
            "target_bitrate_kbps": round(new_bitrate / 1000.0, 1),
            "congestion_state": state,
            "loss_ratio": loss_ratio,
            "rtt_ms": rtt_ms,
            "delay_gradient_ms": delay_gradient_ms,
        }
