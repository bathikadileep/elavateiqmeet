"""
ElevateIQ SFU — RTP Producers
==============================
Represents incoming MediaStreamTracks (Audio, Video, Screen Share)
published to the SFU by meeting participants.
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("elevateiq.sfu.producers")


class Producer:
    """
    SFU Producer representing an incoming WebRTC media track.
    """
    def __init__(
        self,
        transport_id: str,
        kind: str,  # 'audio' or 'video'
        rtp_parameters: Optional[Dict[str, Any]] = None,
        producer_id: Optional[str] = None,
        app_data: Optional[Dict[str, Any]] = None
    ):
        self.id = producer_id or str(uuid.uuid4())
        self.transport_id = transport_id
        self.kind = kind
        self.rtp_parameters = rtp_parameters or {}
        self.app_data = app_data or {}  # e.g., {'peer_sid': '...', 'track_type': 'camera' | 'screen'}
        self.paused = False
        self.closed = False
        self.score = 10  # Media stream quality score (0 - 10)
        self.created_at = time.time()
        self.bytes_received = 0
        self.packets_received = 0
        self.packets_lost = 0

    def pause(self):
        """Pause producer stream transmission."""
        self.paused = True
        log.debug("Producer paused: id=%s, kind=%s", self.id, self.kind)

    def resume(self):
        """Resume producer stream transmission."""
        self.paused = False
        log.debug("Producer resumed: id=%s, kind=%s", self.id, self.kind)

    def close(self):
        """Close producer and release media track resources."""
        if self.closed:
            return
        self.closed = True
        log.info("Producer closed: id=%s, kind=%s", self.id, self.kind)

    def get_stats(self) -> Dict[str, Any]:
        """Returns producer stream performance metrics."""
        return {
            "id": self.id,
            "kind": self.kind,
            "transport_id": self.transport_id,
            "paused": self.paused,
            "score": self.score,
            "bytes_received": self.bytes_received,
            "packets_received": self.packets_received,
            "packets_lost": self.packets_lost,
            "app_data": self.app_data
        }
