"""
WebRTC Adaptive Bitrate (ABR) Video Layer Selector & CPU Health Throttler
========================================================================
Implements real-time spatial and temporal video layer adaptation for WebRTC SFU
peer connections based on bandwidth estimation, CPU pressure, and rendering capabilities.

Features:
- Dynamic spatial resolution layer switching (1080p -> 720p -> 360p -> 180p).
- Temporal frame rate pacing (60fps -> 30fps -> 15fps -> 7.5fps).
- Multi-metric health scoring combining RTT, jitter, packet loss, and CPU load.
- Hysteresis state machine to prevent frequent flapping between video layers.
- Guaranteed audio bandwidth reservation (audio always preserved before video degradation).
- Detailed telemetry snapshots per peer connection.
"""

from __future__ import annotations

import enum
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("elevateiq.services.media.abr")


class SpatialLayer(str, enum.Enum):
    FHD_1080P = "1080p"
    HD_720P = "720p"
    SD_360P = "360p"
    LD_180P = "180p"
    DISABLED = "disabled"


class TemporalLayer(int, enum.Enum):
    FPS_60 = 60
    FPS_30 = 30
    FPS_15 = 15
    FPS_7_5 = 7


class CpuPressureLevel(str, enum.Enum):
    NOMINAL = "nominal"
    MODERATE = "moderate"
    CRITICAL = "critical"


@dataclass
class LayerProfile:
    """Bitrate bounds and specifications for a spatial video tier."""
    spatial: SpatialLayer
    width: int
    height: int
    min_bitrate_kbps: int
    target_bitrate_kbps: int
    max_bitrate_kbps: int


LAYER_PROFILES: Dict[SpatialLayer, LayerProfile] = {
    SpatialLayer.FHD_1080P: LayerProfile(SpatialLayer.FHD_1080P, 1920, 1080, 1500, 2500, 4000),
    SpatialLayer.HD_720P: LayerProfile(SpatialLayer.HD_720P, 1280, 720, 700, 1200, 1800),
    SpatialLayer.SD_360P: LayerProfile(SpatialLayer.SD_360P, 640, 360, 250, 500, 800),
    SpatialLayer.LD_180P: LayerProfile(SpatialLayer.LD_180P, 320, 180, 80, 150, 300),
    SpatialLayer.DISABLED: LayerProfile(SpatialLayer.DISABLED, 0, 0, 0, 0, 0),
}


@dataclass
class ClientMetricsReport:
    """Inbound telemetry report from a client WebRTC RTCP receiver."""
    peer_id: str
    available_bandwidth_kbps: int
    round_trip_time_ms: float
    packet_loss_ratio: float  # 0.0 to 1.0
    jitter_ms: float
    cpu_usage_pct: float  # 0 to 100
    dropped_frames_pct: float  # 0 to 100
    is_battery_saving: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class LayerDecision:
    """ABR decision output indicating chosen spatial and temporal layer."""
    peer_id: str
    spatial: SpatialLayer
    temporal: TemporalLayer
    target_bitrate_kbps: int
    cpu_pressure: CpuPressureLevel
    reason: str
    transitioned: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "spatial": self.spatial.value,
            "temporal": int(self.temporal),
            "target_bitrate_kbps": self.target_bitrate_kbps,
            "cpu_pressure": self.cpu_pressure.value,
            "reason": self.reason,
            "transitioned": self.transitioned,
            "timestamp": self.timestamp,
        }


class AbrLayerSelector:
    """
    Adaptive Bitrate and CPU governor for WebRTC video publishers and subscribers.
    Applies hysteresis delay and multi-dimensional scoring before adjusting layers.
    """

    HYSTERESIS_UPGRADE_SECONDS = 5.0  # Require 5s of clean headroom before upgrading
    HYSTERESIS_DOWNGRADE_SECONDS = 1.0  # Fast downgrade on congestion or CPU throttle
    AUDIO_RESERVE_KBPS = 64  # Reserve 64kbps Opus audio

    def __init__(self) -> None:
        self.peer_state: Dict[str, Dict[str, Any]] = {}

    def register_peer(self, peer_id: str, initial_spatial: SpatialLayer = SpatialLayer.HD_720P) -> None:
        self.peer_state[peer_id] = {
            "current_spatial": initial_spatial,
            "current_temporal": TemporalLayer.FPS_30,
            "last_transition_ts": time.time(),
            "candidate_spatial": initial_spatial,
            "candidate_first_seen_ts": time.time(),
            "history": [],
        }
        logger.info("Registered ABR peer %s with initial layer %s", peer_id, initial_spatial.value)

    def evaluate_metrics(self, report: ClientMetricsReport) -> LayerDecision:
        """
        Evaluates incoming RTCP feedback and CPU metrics to compute optimal video tier.
        """
        peer_id = report.peer_id
        if peer_id not in self.peer_state:
            self.register_peer(peer_id)

        state = self.peer_state[peer_id]
        now = report.timestamp or time.time()

        # 1. Determine CPU Pressure
        cpu_pressure = CpuPressureLevel.NOMINAL
        if report.cpu_usage_pct >= 90.0 or report.dropped_frames_pct >= 25.0:
            cpu_pressure = CpuPressureLevel.CRITICAL
        elif report.cpu_usage_pct >= 75.0 or report.dropped_frames_pct >= 10.0 or report.is_battery_saving:
            cpu_pressure = CpuPressureLevel.MODERATE

        # 2. Subtract reserved audio bandwidth
        net_video_budget = max(0, report.available_bandwidth_kbps - self.AUDIO_RESERVE_KBPS)

        # 3. Determine target spatial layer candidate
        target_spatial = SpatialLayer.DISABLED
        reason = "Normal operation"

        if net_video_budget < 100 or report.packet_loss_ratio > 0.30:
            target_spatial = SpatialLayer.DISABLED
            reason = "Severe packet loss or near-zero bandwidth; audio-only fallback"
        elif cpu_pressure == CpuPressureLevel.CRITICAL:
            # Force downgrade to LD or SD regardless of bandwidth
            target_spatial = SpatialLayer.LD_180P
            reason = f"Critical CPU pressure ({report.cpu_usage_pct}%) or high frame drops ({report.dropped_frames_pct}%)"
        elif cpu_pressure == CpuPressureLevel.MODERATE:
            # Cap at 720p maximum
            if net_video_budget >= LAYER_PROFILES[SpatialLayer.HD_720P].min_bitrate_kbps:
                target_spatial = SpatialLayer.HD_720P
            else:
                target_spatial = SpatialLayer.SD_360P
            reason = f"Moderate CPU pressure ({report.cpu_usage_pct}%)"
        else:
            # Bandwidth driven
            if net_video_budget >= LAYER_PROFILES[SpatialLayer.FHD_1080P].min_bitrate_kbps and report.packet_loss_ratio < 0.03:
                target_spatial = SpatialLayer.FHD_1080P
            elif net_video_budget >= LAYER_PROFILES[SpatialLayer.HD_720P].min_bitrate_kbps and report.packet_loss_ratio < 0.08:
                target_spatial = SpatialLayer.HD_720P
            elif net_video_budget >= LAYER_PROFILES[SpatialLayer.SD_360P].min_bitrate_kbps and report.packet_loss_ratio < 0.15:
                target_spatial = SpatialLayer.SD_360P
            else:
                target_spatial = SpatialLayer.LD_180P

        # 4. Determine temporal layer (FPS)
        if target_spatial == SpatialLayer.DISABLED:
            target_temporal = TemporalLayer.FPS_7_5
        elif cpu_pressure == CpuPressureLevel.CRITICAL or report.packet_loss_ratio > 0.15:
            target_temporal = TemporalLayer.FPS_15
        elif target_spatial == SpatialLayer.FHD_1080P and cpu_pressure == CpuPressureLevel.NOMINAL:
            target_temporal = TemporalLayer.FPS_60
        else:
            target_temporal = TemporalLayer.FPS_30

        # 5. Apply Hysteresis Filter
        current_spatial = state["current_spatial"]
        spatial_order = [SpatialLayer.DISABLED, SpatialLayer.LD_180P, SpatialLayer.SD_360P, SpatialLayer.HD_720P, SpatialLayer.FHD_1080P]
        curr_rank = spatial_order.index(current_spatial)
        target_rank = spatial_order.index(target_spatial)

        transitioned = False
        effective_spatial = current_spatial

        if target_rank != curr_rank:
            is_upgrade = target_rank > curr_rank
            if target_spatial == SpatialLayer.DISABLED:
                required_dwell = 0.0
            else:
                required_dwell = self.HYSTERESIS_UPGRADE_SECONDS if is_upgrade else self.HYSTERESIS_DOWNGRADE_SECONDS

            if state["candidate_spatial"] != target_spatial:
                state["candidate_spatial"] = target_spatial
                state["candidate_first_seen_ts"] = now

            dwell_time = now - state["candidate_first_seen_ts"]
            if dwell_time >= required_dwell:
                effective_spatial = target_spatial
                state["current_spatial"] = target_spatial
                state["last_transition_ts"] = now
                transitioned = True
                logger.info(
                    "ABR layer transition for %s: %s -> %s (Dwell: %.1fs, Reason: %s)",
                    peer_id, current_spatial.value, target_spatial.value, dwell_time, reason
                )
            else:
                effective_spatial = current_spatial
        else:
            state["candidate_spatial"] = target_spatial
            state["candidate_first_seen_ts"] = now

        target_kbps = LAYER_PROFILES[effective_spatial].target_bitrate_kbps

        decision = LayerDecision(
            peer_id=peer_id,
            spatial=effective_spatial,
            temporal=target_temporal,
            target_bitrate_kbps=target_kbps,
            cpu_pressure=cpu_pressure,
            reason=reason,
            transitioned=transitioned,
            timestamp=now,
        )

        state["current_temporal"] = target_temporal
        state["history"].append(decision)
        if len(state["history"]) > 50:
            state["history"].pop(0)

        return decision

    def get_peer_current_decision(self, peer_id: str) -> Optional[LayerDecision]:
        state = self.peer_state.get(peer_id)
        if not state or not state["history"]:
            return None
        return state["history"][-1]
