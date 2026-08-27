"""
ElevateIQ SFU — RTP Consumers
==============================
Represents downstream MediaStreamTracks consumed by meeting participants
subscribing to a remote Producer's stream.
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("elevateiq.sfu.consumers")


class Consumer:
    """
    SFU Consumer representing an outgoing WebRTC media track to a subscriber.
    """
    def __init__(
        self,
        producer_id: str,
        transport_id: str,
        kind: str,
        rtp_parameters: Optional[Dict[str, Any]] = None,
        consumer_id: Optional[str] = None,
        app_data: Optional[Dict[str, Any]] = None
    ):
        self.id = consumer_id or str(uuid.uuid4())
        self.producer_id = producer_id
        self.transport_id = transport_id
        self.kind = kind
        self.rtp_parameters = rtp_parameters or {}
        self.app_data = app_data or {}
        self.paused = False
        self.closed = False
        self.preferred_spatial_layer = 2  # 0: Low (360p), 1: Medium (720p), 2: High (1080p)
        self.current_spatial_layer = 2
        self.score = 10
        self.created_at = time.time()
        self.bytes_sent = 0
        self.packets_sent = 0

    def set_preferred_layers(self, spatial_layer: int, temporal_layer: int = 2):
        """Set downstream simulcast quality layers (0: 360p, 1: 720p, 2: 1080p)."""
        self.preferred_spatial_layer = max(0, min(2, spatial_layer))
        self.current_spatial_layer = self.preferred_spatial_layer
        log.debug("Consumer %s preferred layer set to spatial=%d", self.id, self.preferred_spatial_layer)

    def pause(self):
        """Pause consumer stream transmission."""
        self.paused = True
        log.debug("Consumer paused: id=%s", self.id)

    def resume(self):
        """Resume consumer stream transmission."""
        self.paused = False
        log.debug("Consumer resumed: id=%s", self.id)

    def close(self):
        """Close consumer and release downstream track."""
        if self.closed:
            return
        self.closed = True
        log.info("Consumer closed: id=%s", self.id)

    def get_stats(self) -> Dict[str, Any]:
        """Returns consumer stream transmission statistics."""
        return {
            "id": self.id,
            "producer_id": self.producer_id,
            "transport_id": self.transport_id,
            "kind": self.kind,
            "paused": self.paused,
            "preferred_spatial_layer": self.preferred_spatial_layer,
            "current_spatial_layer": self.current_spatial_layer,
            "score": self.score,
            "bytes_sent": self.bytes_sent,
            "packets_sent": self.packets_sent,
            "app_data": self.app_data
        }
