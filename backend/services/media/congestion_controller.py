"""
ElevateIQ — WebRTC Google Congestion Control (GCC) Estimator
=============================================================
Implements delay-based and loss-based congestion control algorithms (RFC 8888 / GCC).
Calculates inter-arrival delay gradients, maintains adaptive overuse thresholds,
and executes AIMD rate adaptation to maximize video throughput while preventing bufferbloat.
"""

import time
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("elevateiq.services.media.gcc")


class OveruseDetectorState(str, Enum):
    """Delay-based network link overuse states."""
    NORMAL = "normal"
    OVERUSING = "overusing"
    UNDERUSING = "underusing"


class RateControlState(str, Enum):
    """AIMD Rate Control State Machine."""
    INCREASE = "increase"
    HOLD = "hold"
    DECREASE = "decrease"


@dataclass
class PacketFeedback:
    """Represents an RTP feedback report for a packet group."""
    sequence_number: int
    send_timestamp_ms: float
    arrival_timestamp_ms: float
    payload_size_bytes: int


class GoogleCongestionController:
    """
    Standard WebRTC GCC Bandwidth Estimator.
    Combines delay-based trendline filtering with loss-based AIMD rate control.
    """

    MIN_BITRATE_KBPS = 100
    MAX_BITRATE_KBPS = 20000

    def __init__(
        self,
        peer_id: str,
        initial_bitrate_kbps: int = 2000,
        threshold_gamma: float = 12.5
    ):
        self.peer_id = peer_id
        self.target_bitrate_kbps: float = float(initial_bitrate_kbps)
        self.rate_state: RateControlState = RateControlState.INCREASE
        self.detector_state: OveruseDetectorState = OveruseDetectorState.NORMAL

        # Delay trendline state
        self.gamma: float = threshold_gamma  # Dynamic overuse threshold (ms)
        self.k_up: float = 0.0087            # Threshold adaptation rate when increasing
        self.k_down: float = 0.039           # Threshold adaptation rate when decreasing
        self.accumulated_delay_gradient: float = 0.0
        self.last_packet: Optional[PacketFeedback] = None
        self.last_state_change_ts: float = time.time()

    def process_packet_feedback(
        self,
        feedback: PacketFeedback,
        current_time_ms: Optional[float] = None
    ) -> OveruseDetectorState:
        """
        Process packet arrival timing to compute inter-arrival delay gradient.
        Updates overuse detector state and adapts dynamic threshold gamma.
        """
        if self.last_packet is None:
            self.last_packet = feedback
            return OveruseDetectorState.NORMAL

        # Inter-departure time delta
        send_delta = feedback.send_timestamp_ms - self.last_packet.send_timestamp_ms
        # Inter-arrival time delta
        recv_delta = feedback.arrival_timestamp_ms - self.last_packet.arrival_timestamp_ms

        delay_gradient = recv_delta - send_delta
        self.last_packet = feedback

        # Exponential smoothing on delay gradient
        alpha = 0.2
        self.accumulated_delay_gradient = (alpha * delay_gradient) + ((1.0 - alpha) * self.accumulated_delay_gradient)

        # Classify state
        if self.accumulated_delay_gradient > self.gamma:
            self.detector_state = OveruseDetectorState.OVERUSING
        elif self.accumulated_delay_gradient < -self.gamma:
            self.detector_state = OveruseDetectorState.UNDERUSING
        else:
            self.detector_state = OveruseDetectorState.NORMAL

        # Adapt threshold gamma dynamically
        now_ms = current_time_ms or (time.time() * 1000.0)
        k = self.k_up if abs(self.accumulated_delay_gradient) > self.gamma else self.k_down
        self.gamma = max(6.0, min(60.0, self.gamma + (abs(self.accumulated_delay_gradient) - self.gamma) * k))

        return self.detector_state

    def update_loss_feedback(self, packet_loss_fraction: float) -> float:
        """
        Execute AIMD (Additive Increase / Multiplicative Decrease) rate adaptation
        based on reported receiver RTCP packet loss fraction (0.0 to 1.0).
        """
        loss_pct = packet_loss_fraction * 100.0

        if loss_pct > 10.0 or self.detector_state == OveruseDetectorState.OVERUSING:
            # Multiplicative Decrease (backoff)
            self.rate_state = RateControlState.DECREASE
            backoff_factor = 0.85
            self.target_bitrate_kbps = max(
                self.MIN_BITRATE_KBPS,
                self.target_bitrate_kbps * backoff_factor
            )
            log.warning("GCC [%s]: Rate decrease to %.0f kbps (Loss: %.1f%%, Delay State: %s)",
                        self.peer_id, self.target_bitrate_kbps, loss_pct, self.detector_state.value)

        elif loss_pct >= 2.0:
            # Hold current rate
            self.rate_state = RateControlState.HOLD

        else:
            # Additive Increase
            self.rate_state = RateControlState.INCREASE
            additive_step = max(50.0, self.target_bitrate_kbps * 0.08)
            self.target_bitrate_kbps = min(
                self.MAX_BITRATE_KBPS,
                self.target_bitrate_kbps + additive_step
            )

        return round(self.target_bitrate_kbps, 0)

    def get_controller_state(self) -> Dict[str, Any]:
        """Return diagnostic metrics of the congestion controller."""
        return {
            "peer_id": self.peer_id,
            "target_bitrate_kbps": round(self.target_bitrate_kbps, 0),
            "rate_state": self.rate_state.value,
            "detector_state": self.detector_state.value,
            "delay_gradient_ms": round(self.accumulated_delay_gradient, 2),
            "dynamic_threshold_gamma": round(self.gamma, 2)
        }
