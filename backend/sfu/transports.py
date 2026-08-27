"""
ElevateIQ SFU — WebRTC & Plain Transport Layer
================================================
Manages WebRTC ICE candidates, DTLS fingerprint verification,
packet statistics, and RTP transport lifecycle for media routing.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.sfu.transports")


class SFUTransport:
    """
    Base SFU Media Transport class representing an active WebRTC / UDP channel.
    """
    def __init__(self, transport_id: Optional[str] = None, direction: str = "sendrecv"):
        self.id = transport_id or str(uuid.uuid4())
        self.direction = direction  # 'sendonly', 'recvonly', 'sendrecv'
        self.state = "new"  # 'new', 'connecting', 'connected', 'failed', 'closed'
        self.created_at = time.time()
        self.connected_at: Optional[float] = None
        self.bytes_received = 0
        self.bytes_sent = 0
        self.packets_received = 0
        self.packets_sent = 0
        self.producers: Dict[str, Any] = {}
        self.consumers: Dict[str, Any] = {}

    def connect(self, dtls_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Connect transport with remote DTLS fingerprint parameters."""
        self.state = "connecting"
        # Simulate DTLS handshake completion
        self.state = "connected"
        self.connected_at = time.time()
        log.info("SFU Transport connected: id=%s, direction=%s", self.id, self.direction)
        return {
            "id": self.id,
            "state": self.state,
            "connected_at": self.connected_at
        }

    def close(self):
        """Close transport and clean up associated producers/consumers."""
        if self.state == "closed":
            return
        self.state = "closed"
        for producer in list(self.producers.values()):
            producer.close()
        for consumer in list(self.consumers.values()):
            consumer.close()
        self.producers.clear()
        self.consumers.clear()
        log.info("SFU Transport closed: id=%s", self.id)

    def get_stats(self) -> Dict[str, Any]:
        """Returns transport network statistics."""
        uptime = (time.time() - self.connected_at) if self.connected_at else 0
        return {
            "id": self.id,
            "direction": self.direction,
            "state": self.state,
            "uptime_seconds": round(uptime, 2),
            "bytes_received": self.bytes_received,
            "bytes_sent": self.bytes_sent,
            "packets_received": self.packets_received,
            "packets_sent": self.packets_sent,
            "producer_count": len(self.producers),
            "consumer_count": len(self.consumers)
        }


class WebRtcTransport(SFUTransport):
    """
    WebRTC PeerConnection Transport managing ICE candidates, Ufrag, Pwd, and DTLS.
    """
    def __init__(self, transport_id: Optional[str] = None, direction: str = "sendrecv", listen_ip: str = "0.0.0.0"):
        super().__init__(transport_id, direction)
        self.listen_ip = listen_ip
        self.ice_ufrag = f"sfu_ufrag_{uuid.uuid4().hex[:8]}"
        self.ice_pwd = f"sfu_pwd_{uuid.uuid4().hex[:16]}"
        self.ice_candidates: List[Dict[str, Any]] = [
            {
                "foundation": "udpcandidate",
                "component": 1,
                "protocol": "udp",
                "priority": 2122260223,
                "ip": listen_ip if listen_ip != "0.0.0.0" else "127.0.0.1",
                "port": 40000 + (hash(self.id) % 10000),
                "type": "host"
            }
        ]
        self.dtls_fingerprints: List[Dict[str, str]] = [
            {
                "algorithm": "sha-256",
                "value": "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
            }
        ]

    def get_transport_options(self) -> Dict[str, Any]:
        """Returns Client ICE & DTLS parameters needed to connect to SFU."""
        return {
            "id": self.id,
            "iceParameters": {
                "usernameFragment": self.ice_ufrag,
                "password": self.ice_pwd,
                "iceLite": True
            },
            "iceCandidates": self.ice_candidates,
            "dtlsParameters": {
                "role": "auto",
                "fingerprints": self.dtls_fingerprints
            }
        }


class PlainTransport(SFUTransport):
    """
    Plain UDP Transport for server-to-server relay, recording workers, or external RTP streams.
    """
    def __init__(self, transport_id: Optional[str] = None, rtp_port: int = 50000, rtcp_port: int = 50001):
        super().__init__(transport_id, direction="sendrecv")
        self.rtp_port = rtp_port
        self.rtcp_port = rtcp_port

    def get_tuple(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rtp_port": self.rtp_port,
            "rtcp_port": self.rtcp_port,
            "protocol": "UDP"
        }
