"""
ElevateIQ — WebRTC Adaptive Bitrate & Simulcast Control Engine
================================================================
Manages dynamic WebRTC Simulcast spatial layers (Low/Medium/High), Scalable Video Coding (SVC),
REMB/GCC bandwidth estimation adjustments, and automatic resolution downscaling.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

log = logging.getLogger("elevateiq.services.adaptive_bitrate")


class AdaptiveBitrateEngine:
    """Enterprise WebRTC Simulcast & Congestion Control Engine."""

    SIMULCAST_LAYERS = {
        "low": {"max_bitrate_kbps": 150, "width": 320, "height": 180, "fps": 15},
        "medium": {"max_bitrate_kbps": 500, "width": 640, "height": 360, "fps": 24},
        "high": {"max_bitrate_kbps": 2000, "width": 1280, "height": 720, "fps": 30},
        "full_hd": {"max_bitrate_kbps": 4500, "width": 1920, "height": 1080, "fps": 60},
    }

    def __init__(self):
        self._peer_states: Dict[str, Dict[str, Any]] = {}

    def register_peer(self, peer_id: str, initial_bandwidth_kbps: float = 2500.0) -> Dict[str, Any]:
        """Register a new WebRTC peer connection for bitrate tracking."""
        state = {
            "peer_id": peer_id,
            "estimated_bandwidth_kbps": initial_bandwidth_kbps,
            "active_layer": "high",
            "target_resolution": "1280x720",
            "target_fps": 30,
            "congestion_state": "NORMAL",
            "dropped_frames_count": 0,
        }
        self._peer_states[peer_id] = state
        log.info("Registered peer %s for adaptive bitrate control (initial BW: %.1f kbps)", peer_id, initial_bandwidth_kbps)
        return state

    def update_bandwidth_estimate(self, peer_id: str, new_estimated_kbps: float, packet_loss_pct: float) -> Dict[str, Any]:
        """
        Process Google Congestion Control (GCC) or Transport-Wide CC (TWCC) feedback signal
        and adapt active simulcast spatial layer.
        """
        if peer_id not in self._peer_states:
            self.register_peer(peer_id, new_estimated_kbps)

        peer = self._peer_states[peer_id]
        peer["estimated_bandwidth_kbps"] = new_estimated_kbps

        # Congestion State Evaluation
        if packet_loss_pct >= 0.10 or new_estimated_kbps < 250:
            peer["congestion_state"] = "HEAVY_CONGESTION"
            new_layer = "low"
        elif packet_loss_pct >= 0.04 or new_estimated_kbps < 800:
            peer["congestion_state"] = "MODERATE_CONGESTION"
            new_layer = "medium"
        elif new_estimated_kbps >= 3500:
            peer["congestion_state"] = "OPTIMAL"
            new_layer = "full_hd"
        else:
            peer["congestion_state"] = "NORMAL"
            new_layer = "high"

        # Apply Layer Transition
        if new_layer != peer["active_layer"]:
            log.info("Adapting Simulcast layer for peer %s: %s -> %s (BW: %.1f kbps, Loss: %.1f%%)",
                     peer_id, peer["active_layer"], new_layer, new_estimated_kbps, packet_loss_pct * 100)
            peer["active_layer"] = new_layer

        layer_info = self.SIMULCAST_LAYERS[new_layer]
        peer["target_resolution"] = f"{layer_info['width']}x{layer_info['height']}"
        peer["target_fps"] = layer_info["fps"]

        return peer

    def get_peer_state(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Get current bitrate adaptation state for peer."""
        return self._peer_states.get(peer_id)

    def calculate_active_stream_config(self, peer_ids: List[str]) -> Dict[str, Any]:
        """
        Calculate total SFU egress load across multiple connected peers.
        """
        total_kbps = 0.0
        layer_counts = {"low": 0, "medium": 0, "high": 0, "full_hd": 0}

        for pid in peer_ids:
            pstate = self._peer_states.get(pid)
            if pstate:
                layer = pstate["active_layer"]
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
                total_kbps += self.SIMULCAST_LAYERS[layer]["max_bitrate_kbps"]

        return {
            "active_peers_count": len(peer_ids),
            "aggregate_egress_kbps": total_kbps,
            "layer_distribution": layer_counts,
        }
