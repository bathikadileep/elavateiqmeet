"""
ElevateIQ — Selective Forwarding Unit (SFU) Media Engine
=========================================================
Enterprise WebRTC Media Architecture supporting 100+ participant rooms,
simulcast quality layer scaling, Voice Activity Detection (VAD),
and low-latency RTP transport routing.
"""

from backend.sfu.worker import SFUWorkerPool, get_sfu_worker_pool
from backend.sfu.router import SFURouter, get_or_create_sfu_router, destroy_sfu_router
from backend.sfu.transports import SFUTransport, WebRtcTransport, PlainTransport
from backend.sfu.producers import Producer
from backend.sfu.consumers import Consumer
from backend.sfu.simulcast import SimulcastEngine, SimulcastLayer
from backend.sfu.vad import VoiceActivityDetector, VADEvent

__all__ = [
    "SFUWorkerPool",
    "get_sfu_worker_pool",
    "SFURouter",
    "get_or_create_sfu_router",
    "destroy_sfu_router",
    "SFUTransport",
    "WebRtcTransport",
    "PlainTransport",
    "Producer",
    "Consumer",
    "SimulcastEngine",
    "SimulcastLayer",
    "VoiceActivityDetector",
    "VADEvent",
]
