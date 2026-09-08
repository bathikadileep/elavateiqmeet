"""
ElevateIQ — WebRTC Simulcast Layer Controller & Traffic Shaper
===============================================================
Orchestrates spatial and temporal layer switching (SVC / Simulcast) on the SFU router.
Employs a token-bucket packet pacer to smooth outbound RTP bursts and dynamically adapts
layer subscription based on active speaker dominance and receiver CPU constraints.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("elevateiq.services.media.simulcast")


class SpatialLayer(int, Enum):
    """Simulcast spatial video layers."""
    LOW = 0       # 320x180 @ 15fps (100 kbps)
    MEDIUM = 1    # 640x360 @ 30fps (450 kbps)
    HIGH = 2      # 1280x720 @ 30fps (1500 kbps)
    ULTRA = 3     # 1920x1080 @ 60fps (3500 kbps)


@dataclass
class LayerSpec:
    """Specification of a single simulcast encoding layer."""
    layer: SpatialLayer
    width: int
    height: int
    fps: int
    target_bitrate_kbps: int


@dataclass
class ReceiverSubscription:
    """Tracks a receiving peer's subscribed simulcast layer for a producer stream."""
    receiver_id: str
    producer_id: str
    current_layer: SpatialLayer
    target_layer: SpatialLayer
    is_active_speaker: bool = False
    is_screen_share: bool = False
    cpu_overused: bool = False
    last_switched_at: float = 0.0


class LeakyBucketPacer:
    """
    Token-bucket traffic shaper for RTP video packet pacing.
    Prevents burst packet loss over low-buffer network segments.
    """

    def __init__(self, target_bitrate_kbps: int = 2500, max_queue_bytes: int = 500000):
        self.target_bitrate_kbps = target_bitrate_kbps
        self.max_queue_bytes = max_queue_bytes
        self.bucket_bytes = 0.0
        self.max_bucket_bytes = (target_bitrate_kbps * 1000 // 8) * 0.05  # 50ms burst window
        self.last_leak_time = time.time()
        self.queue: List[Tuple[int, bytes]] = []  # (size_bytes, packet_data)
        self.current_queue_bytes = 0

    def update_rate(self, new_bitrate_kbps: int) -> None:
        """Dynamically adapt pacer throughput to match estimated bandwidth."""
        self.target_bitrate_kbps = max(64, new_bitrate_kbps)
        self.max_bucket_bytes = (self.target_bitrate_kbps * 1000 // 8) * 0.05

    def enqueue_packet(self, packet_bytes: bytes) -> bool:
        """Enqueue an RTP packet into the pacing queue. Returns False if queue full."""
        pkt_len = len(packet_bytes)
        if self.current_queue_bytes + pkt_len > self.max_queue_bytes:
            log.warning("Pacer: Queue overflow (%d bytes). Dropping packet.", self.current_queue_bytes)
            return False
        self.queue.append((pkt_len, packet_bytes))
        self.current_queue_bytes += pkt_len
        return True

    def process_pacing(self, current_time: Optional[float] = None) -> List[bytes]:
        """
        Leak tokens and transmit eligible paced packets.
        Returns list of packets cleared for immediate network transmission.
        """
        now = current_time or time.time()
        elapsed = now - self.last_leak_time
        self.last_leak_time = now

        # Add tokens: bytes = (bitrate_kbps * 1000 / 8) * elapsed
        leak_capacity = (self.target_bitrate_kbps * 1000 / 8.0) * elapsed
        self.bucket_bytes = min(self.max_bucket_bytes, self.bucket_bytes + leak_capacity)

        released_packets: List[bytes] = []
        while self.queue:
            pkt_len, pkt_data = self.queue[0]
            if self.bucket_bytes >= pkt_len:
                self.bucket_bytes -= pkt_len
                self.current_queue_bytes -= pkt_len
                released_packets.append(self.queue.pop(0)[1])
            else:
                break

        return released_packets


class SimulcastLayerController:
    """
    SFU Simulcast & Scalable Video Coding (SVC) Layer Allocator.
    Manages dynamic spatial layer switching based on bandwidth, speaker priority, and CPU.
    """

    LAYER_SPECS: Dict[SpatialLayer, LayerSpec] = {
        SpatialLayer.LOW: LayerSpec(SpatialLayer.LOW, 320, 180, 15, 100),
        SpatialLayer.MEDIUM: LayerSpec(SpatialLayer.MEDIUM, 640, 360, 30, 450),
        SpatialLayer.HIGH: LayerSpec(SpatialLayer.HIGH, 1280, 720, 30, 1500),
        SpatialLayer.ULTRA: LayerSpec(SpatialLayer.ULTRA, 1920, 1080, 60, 3500)
    }

    LAYER_HYSTERESIS_SEC = 2.0  # Minimum delay between layer switches to prevent rapid oscillation

    def __init__(self, room_code: str):
        self.room_code = room_code
        self.subscriptions: Dict[Tuple[str, str], ReceiverSubscription] = {}
        self.active_speaker_id: Optional[str] = None

    def subscribe(
        self,
        receiver_id: str,
        producer_id: str,
        initial_layer: SpatialLayer = SpatialLayer.MEDIUM,
        is_screen_share: bool = False
    ) -> ReceiverSubscription:
        """Register a receiver's subscription to a video producer."""
        sub = ReceiverSubscription(
            receiver_id=receiver_id,
            producer_id=producer_id,
            current_layer=initial_layer,
            target_layer=initial_layer,
            is_screen_share=is_screen_share
        )
        self.subscriptions[(receiver_id, producer_id)] = sub
        log.info("SimulcastController [%s]: %s subscribed to %s at layer %s",
                 self.room_code, receiver_id, producer_id, initial_layer.name)
        return sub

    def set_active_speaker(self, speaker_id: Optional[str]) -> None:
        """Update active speaker dominance across all consumer subscriptions."""
        self.active_speaker_id = speaker_id
        for (rec_id, prod_id), sub in self.subscriptions.items():
            sub.is_active_speaker = (prod_id == speaker_id)

    def set_cpu_overuse(self, receiver_id: str, is_overused: bool) -> None:
        """Notify controller of receiver local hardware or decoder overload."""
        for (rec_id, prod_id), sub in self.subscriptions.items():
            if rec_id == receiver_id:
                sub.cpu_overused = is_overused

    def compute_optimal_layer(
        self,
        receiver_id: str,
        producer_id: str,
        downlink_bandwidth_kbps: int
    ) -> SpatialLayer:
        """
        Evaluate ideal simulcast layer based on available downlink bandwidth,
        speaker priority, screen-share flag, and CPU load.
        """
        sub = self.subscriptions.get((receiver_id, producer_id))
        if not sub:
            return SpatialLayer.LOW

        # Screen share always prioritizes HIGH or ULTRA if bandwidth permits
        if sub.is_screen_share:
            if downlink_bandwidth_kbps >= 2500 and not sub.cpu_overused:
                return SpatialLayer.ULTRA
            elif downlink_bandwidth_kbps >= 1200:
                return SpatialLayer.HIGH
            return SpatialLayer.MEDIUM

        # CPU Overused -> Downgrade immediately
        if sub.cpu_overused:
            return SpatialLayer.LOW

        # Active speaker receives top available layer
        if sub.is_active_speaker:
            if downlink_bandwidth_kbps >= 3200:
                return SpatialLayer.ULTRA
            elif downlink_bandwidth_kbps >= 1400:
                return SpatialLayer.HIGH
            elif downlink_bandwidth_kbps >= 400:
                return SpatialLayer.MEDIUM
            return SpatialLayer.LOW

        # Thumbnail / Non-dominant participant grid
        if downlink_bandwidth_kbps >= 2000:
            return SpatialLayer.MEDIUM
        return SpatialLayer.LOW

    def step_layer_switch(
        self,
        receiver_id: str,
        producer_id: str,
        downlink_bandwidth_kbps: int,
        current_time: Optional[float] = None
    ) -> Tuple[bool, SpatialLayer]:
        """
        Evaluate and execute layer switch with hysteresis dampening.
        Returns (switched: bool, current_active_layer: SpatialLayer).
        """
        key = (receiver_id, producer_id)
        sub = self.subscriptions.get(key)
        if not sub:
            return False, SpatialLayer.LOW

        now = current_time or time.time()
        target = self.compute_optimal_layer(receiver_id, producer_id, downlink_bandwidth_kbps)
        sub.target_layer = target

        # Check if layer change needed
        if target == sub.current_layer:
            return False, sub.current_layer

        # Enforce hysteresis dampening for upgrades (downgrades happen immediately)
        is_upgrade = target.value > sub.current_layer.value
        if is_upgrade and (now - sub.last_switched_at) < self.LAYER_HYSTERESIS_SEC:
            return False, sub.current_layer

        # Apply switch
        old_layer = sub.current_layer
        sub.current_layer = target
        sub.last_switched_at = now
        log.info("SimulcastController [%s]: Switched %s -> %s from %s to %s",
                 self.room_code, receiver_id, producer_id, old_layer.name, target.name)
        return True, target
