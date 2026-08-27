"""
ElevateIQ SFU — Room SFU Router
================================
Manages media stream routing, transports, producers, consumers,
and Voice Activity Detection (VAD) per meeting room.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.sfu.transports import WebRtcTransport, SFUTransport
from backend.sfu.producers import Producer
from backend.sfu.consumers import Consumer
from backend.sfu.vad import VoiceActivityDetector, VADEvent

log = logging.getLogger("elevateiq.sfu.router")

_SFU_ROUTERS: Dict[str, "SFURouter"] = {}


class SFURouter:
    """
    SFU Router instance assigned to a specific meeting room code.
    """
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.created_at = time.time()
        self.transports: Dict[str, SFUTransport] = {}
        self.producers: Dict[str, Producer] = {}
        self.consumers: Dict[str, Consumer] = {}
        self.vad = VoiceActivityDetector()

    def create_web_rtc_transport(self, direction: str = "sendrecv") -> WebRtcTransport:
        """Create a new WebRTC transport for a participant."""
        transport = WebRtcTransport(direction=direction)
        self.transports[transport.id] = transport
        log.info("SFU Router [%s]: Created WebRTC transport %s (%s)", self.room_code, transport.id, direction)
        return transport

    def create_producer(
        self, transport_id: str, kind: str, rtp_parameters: Optional[Dict[str, Any]] = None, app_data: Optional[Dict[str, Any]] = None
    ) -> Producer:
        """Create a new media producer on a transport."""
        transport = self.transports.get(transport_id)
        if not transport:
            raise ValueError(f"Transport {transport_id} not found")

        producer = Producer(transport_id=transport_id, kind=kind, rtp_parameters=rtp_parameters, app_data=app_data)
        self.producers[producer.id] = producer
        transport.producers[producer.id] = producer
        log.info("SFU Router [%s]: Created producer %s (%s)", self.room_code, producer.id, kind)
        return producer

    def create_consumer(
        self, producer_id: str, transport_id: str, rtp_parameters: Optional[Dict[str, Any]] = None, app_data: Optional[Dict[str, Any]] = None
    ) -> Consumer:
        """Create a new consumer subscribing to a producer."""
        producer = self.producers.get(producer_id)
        if not producer:
            raise ValueError(f"Producer {producer_id} not found")

        transport = self.transports.get(transport_id)
        if not transport:
            raise ValueError(f"Transport {transport_id} not found")

        consumer = Consumer(
            producer_id=producer_id,
            transport_id=transport_id,
            kind=producer.kind,
            rtp_parameters=rtp_parameters,
            app_data=app_data
        )
        self.consumers[consumer.id] = consumer
        transport.consumers[consumer.id] = consumer
        log.info("SFU Router [%s]: Created consumer %s -> producer %s", self.room_code, consumer.id, producer_id)
        return consumer

    def process_vad_energy(self, sid: str, display_name: str, user_id: Optional[str], dbfs: float) -> Optional[VADEvent]:
        """Process VAD audio energy for active speaker election."""
        return self.vad.process_audio_energy(sid, display_name, user_id, dbfs)

    def close_transport(self, transport_id: str):
        """Close transport and purge associated producers and consumers."""
        transport = self.transports.pop(transport_id, None)
        if transport:
            for p_id in list(transport.producers.keys()):
                self.producers.pop(p_id, None)
            for c_id in list(transport.consumers.keys()):
                self.consumers.pop(c_id, None)
            transport.close()

    def get_stats(self) -> Dict[str, Any]:
        """Returns room SFU statistics."""
        return {
            "room_code": self.room_code,
            "transport_count": len(self.transports),
            "producer_count": len(self.producers),
            "consumer_count": len(self.consumers),
            "active_speaker": self.vad.active_speaker_name,
            "uptime_seconds": round(time.time() - self.created_at, 2)
        }

    def close(self):
        """Shutdown router and close all transports."""
        for transport in list(self.transports.values()):
            transport.close()
        self.transports.clear()
        self.producers.clear()
        self.consumers.clear()
        log.info("SFU Router [%s] closed.", self.room_code)


def get_or_create_sfu_router(room_code: str) -> SFURouter:
    """Factory helper to fetch or instantiate a room SFU router."""
    if room_code not in _SFU_ROUTERS:
        _SFU_ROUTERS[room_code] = SFURouter(room_code)
    return _SFU_ROUTERS[room_code]


def destroy_sfu_router(room_code: str):
    """Shutdown and purge a room SFU router."""
    router = _SFU_ROUTERS.pop(room_code, None)
    if router:
        router.close()
