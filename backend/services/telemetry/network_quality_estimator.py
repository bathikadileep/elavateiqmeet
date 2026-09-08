"""
ElevateIQ — WebRTC Network Quality Estimator & Bandwidth Prober
================================================================
Monitors peer connection telemetry (RTT, jitter, burst packet loss), calculates
MOS (Mean Opinion Score) via ITU-T G.107 E-model, and computes adaptive
Simulcast/SVC video layer recommendations.
"""

import math
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("elevateiq.services.telemetry.quality")


class CongestionState(str, Enum):
    """Network congestion severity level."""
    EXCELLENT = "excellent"      # Low RTT (< 50ms), zero loss, MOS > 4.2
    GOOD = "good"                # RTT < 120ms, loss < 2%, MOS > 3.8
    FAIR = "fair"                # RTT < 250ms, loss < 5%, MOS > 3.2
    CONSTRAINED = "constrained"  # RTT < 450ms, loss < 12%, MOS > 2.5
    CRITICAL = "critical"        # High RTT (> 450ms) or loss > 12%, MOS <= 2.5


@dataclass
class VideoLayerPreset:
    """Recommended video encoding profile."""
    profile_name: str
    width: int
    height: int
    fps: int
    target_bitrate_kbps: int
    audio_only: bool = False


class NetworkQualityEstimator:
    """
    Real-time WebRTC Network Telemetry & Quality Evaluation Engine.
    Employs Kalman-smoothed RTT tracking and ITU-T G.107 E-model calculations.
    """

    # Video quality presets
    PRESET_4K = VideoLayerPreset("4K_UHD", 3840, 2160, 30, 8000)
    PRESET_1080P = VideoLayerPreset("FHD_1080P", 1920, 1080, 30, 3500)
    PRESET_720P = VideoLayerPreset("HD_720P", 1280, 720, 30, 1500)
    PRESET_360P = VideoLayerPreset("SD_360P", 640, 360, 24, 500)
    PRESET_AUDIO_ONLY = VideoLayerPreset("AUDIO_ONLY", 0, 0, 0, 32, audio_only=True)

    def __init__(self, peer_id: str, room_code: str):
        self.peer_id = peer_id
        self.room_code = room_code

        # Kalman Filter state for RTT
        self.estimated_rtt_ms: float = 60.0
        self.rtt_variance: float = 100.0
        self.process_noise: float = 4.0
        self.measurement_noise: float = 16.0

        # Running metrics
        self.last_jitter_ms: float = 5.0
        self.last_packet_loss_pct: float = 0.0
        self.estimated_bandwidth_kbps: float = 2500.0
        self.recent_loss_bursts: int = 0
        self.last_update_timestamp: float = time.time()

    def update_telemetry(
        self,
        measured_rtt_ms: float,
        jitter_ms: float,
        packet_loss_pct: float,
        rx_bitrate_kbps: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Ingest raw WebRTC getStats() reports and update smoothed state.
        Updates Kalman RTT filter, detects loss bursts, and computes MOS.
        """
        now = time.time()
        self.last_update_timestamp = now
        self.last_jitter_ms = max(0.0, jitter_ms)
        self.last_packet_loss_pct = max(0.0, min(100.0, packet_loss_pct))

        # Kalman Filter update for RTT
        # 1. Predict
        predicted_variance = self.rtt_variance + self.process_noise
        # 2. Update
        kalman_gain = predicted_variance / (predicted_variance + self.measurement_noise)
        self.estimated_rtt_ms = self.estimated_rtt_ms + kalman_gain * (measured_rtt_ms - self.estimated_rtt_ms)
        self.rtt_variance = (1.0 - kalman_gain) * predicted_variance

        # Detect burst packet loss (> 8% sudden jump)
        if packet_loss_pct >= 8.0:
            self.recent_loss_bursts += 1
            log.warning("QualityEstimator [%s]: Packet loss burst detected (%.1f%%) for peer %s",
                        self.room_code, packet_loss_pct, self.peer_id)

        # Estimate available bandwidth
        if rx_bitrate_kbps and rx_bitrate_kbps > 0:
            # Loss-responsive bandwidth backoff (AIMD: Additive Increase Multiplicative Decrease)
            if packet_loss_pct > 10.0:
                self.estimated_bandwidth_kbps = max(64.0, rx_bitrate_kbps * 0.7)
            elif packet_loss_pct > 3.0:
                self.estimated_bandwidth_kbps = max(128.0, rx_bitrate_kbps * 0.88)
            else:
                self.estimated_bandwidth_kbps = min(15000.0, rx_bitrate_kbps * 1.08 + 100.0)

        mos = self.calculate_mos()
        state = self.classify_congestion()
        preset = self.recommend_video_preset()

        return {
            "peer_id": self.peer_id,
            "smoothed_rtt_ms": round(self.estimated_rtt_ms, 1),
            "jitter_ms": round(self.last_jitter_ms, 1),
            "loss_pct": round(self.last_packet_loss_pct, 2),
            "estimated_bandwidth_kbps": round(self.estimated_bandwidth_kbps, 0),
            "mos_score": round(mos, 2),
            "congestion_state": state.value,
            "recommended_preset": preset.profile_name,
            "audio_only": preset.audio_only
        }

    def calculate_mos(self) -> float:
        """
        Calculate Voice Mean Opinion Score (MOS) from 1.0 (bad) to 4.5 (toll quality).
        Based on ITU-T G.107 E-model:
            R = 93.2 - Id(delay) - Ie(packet loss)
        """
        # Delay impairment: Id
        one_way_delay = (self.estimated_rtt_ms / 2.0) + self.last_jitter_ms
        if one_way_delay <= 150.0:
            id_delay = 0.024 * one_way_delay
        else:
            id_delay = 0.024 * 150.0 + 0.11 * (one_way_delay - 150.0)

        # Packet loss impairment: Ie (Opus codec baseline with PLC)
        ie_loss = 30.0 * math.log(1.0 + 15.0 * (self.last_packet_loss_pct / 100.0))

        r_factor = max(0.0, min(100.0, 93.2 - id_delay - ie_loss))

        # Convert R-factor to MOS (1.0 to 4.5 scale)
        if r_factor < 0:
            return 1.0
        elif r_factor > 100:
            return 4.5

        mos = 1.0 + (0.035 * r_factor) + (7.1e-6 * r_factor * (r_factor - 60.0) * (100.0 - r_factor))
        return max(1.0, min(4.5, mos))

    def classify_congestion(self) -> CongestionState:
        """Classify network link quality into tiered congestion states."""
        rtt = self.estimated_rtt_ms
        loss = self.last_packet_loss_pct
        mos = self.calculate_mos()

        if rtt > 450.0 or loss > 15.0 or mos <= 2.2:
            return CongestionState.CRITICAL
        elif rtt > 250.0 or loss > 6.0 or mos <= 3.0:
            return CongestionState.CONSTRAINED
        elif rtt > 120.0 or loss > 2.5 or mos <= 3.6:
            return CongestionState.FAIR
        elif rtt > 60.0 or loss > 0.5 or mos <= 4.0:
            return CongestionState.GOOD
        else:
            return CongestionState.EXCELLENT

    def recommend_video_preset(self) -> VideoLayerPreset:
        """
        Determine optimal video encoding resolution and framerate based on
        available bandwidth and network stability.
        """
        state = self.classify_congestion()
        bw = self.estimated_bandwidth_kbps

        if state == CongestionState.CRITICAL or bw < 150.0:
            return self.PRESET_AUDIO_ONLY
        elif state == CongestionState.CONSTRAINED or bw < 600.0:
            return self.PRESET_360P
        elif state == CongestionState.FAIR or bw < 1800.0:
            return self.PRESET_720P
        elif state == CongestionState.GOOD or bw < 5000.0:
            return self.PRESET_1080P
        else:
            return self.PRESET_4K

    def should_trigger_fec_boost(self) -> Tuple[bool, int]:
        """
        Evaluate whether forward error correction (FEC) redundancy should be elevated.
        Returns (should_boost: bool, recommended_fec_percent: int).
        """
        if self.last_packet_loss_pct >= 10.0:
            return True, 40  # 40% FEC payload overhead
        elif self.last_packet_loss_pct >= 4.0:
            return True, 20  # 20% FEC overhead
        return False, 0
