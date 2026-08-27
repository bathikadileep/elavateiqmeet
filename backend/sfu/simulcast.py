"""
ElevateIQ SFU — Simulcast Quality Layer Engine
===============================================
Manages multi-stream video simulcast layers (1080p, 720p, 360p)
and handles dynamic bitrate adaptation based on downstream client network stats.
"""

import logging
from typing import Dict, Any, List

log = logging.getLogger("elevateiq.sfu.simulcast")


class SimulcastLayer:
    """Represents a single simulcast video quality level."""
    def __init__(self, index: int, name: str, width: int, height: int, frame_rate: int, max_bitrate_kbps: int):
        self.index = index
        self.name = name
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.max_bitrate_kbps = max_bitrate_kbps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "resolution": f"{self.width}x{self.height}",
            "frame_rate": self.frame_rate,
            "max_bitrate_kbps": self.max_bitrate_kbps
        }


# Standard Enterprise Video Layers
SIMULCAST_LAYERS: List[SimulcastLayer] = [
    SimulcastLayer(index=0, name="low", width=480, height=360, frame_rate=15, max_bitrate_kbps=200),
    SimulcastLayer(index=1, name="medium", width=854, height=480, frame_rate=24, max_bitrate_kbps=600),
    SimulcastLayer(index=2, name="high", width=1280, height=720, frame_rate=30, max_bitrate_kbps=1500)
]


class SimulcastEngine:
    """
    Calculates dynamic layer adaptation based on network loss & RTT latency.
    """

    @staticmethod
    def get_supported_layers() -> List[Dict[str, Any]]:
        return [layer.to_dict() for layer in SIMULCAST_LAYERS]

    @staticmethod
    def calculate_optimal_layer(rtt_ms: float, packet_loss_percent: float, available_bitrate_kbps: float) -> int:
        """
        Determines optimal spatial layer (0: low, 1: medium, 2: high).
        """
        if packet_loss_percent > 8.0 or rtt_ms > 400 or available_bitrate_kbps < 350:
            return 0  # Low (360p)

        if packet_loss_percent > 3.0 or rtt_ms > 200 or available_bitrate_kbps < 850:
            return 1  # Medium (720p)

        return 2  # High (1080p)
