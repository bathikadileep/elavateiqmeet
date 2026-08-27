"""
ElevateIQ — Socket.IO SFU Signaling Handlers
=============================================
Socket event handlers for SFU WebRTC signaling:
  - sfu_get_router_capabilities → Get RTP codecs & extension headers
  - sfu_create_transport        → Allocate new WebRTC Transport on SFU
  - sfu_connect_transport       → Connect client DTLS parameters to Transport
  - sfu_produce                 → Publish incoming media stream track (Audio/Video/Screen)
  - sfu_consume                 → Subscribe to remote producer stream track
  - sfu_set_preferred_layers    → Adjust simulcast quality layer (0: 360p, 1: 720p, 2: 1080p)
  - sfu_vad_energy              → Report VAD audio energy & broadcast active speaker
"""

import logging
from flask import request
from flask_socketio import emit
from backend.sockets.connection import ACTIVE_SOCKETS
from backend.sfu.worker import get_sfu_worker_pool
from backend.sfu.router import get_or_create_sfu_router
from backend.sfu.simulcast import SimulcastEngine

log = logging.getLogger("elevateiq.sockets.sfu_signaling")


def register_sfu_signaling_handlers(sio):

    @sio.on("sfu_get_router_capabilities")
    def handle_get_capabilities(data):
        pool = get_sfu_worker_pool()
        emit("sfu_router_capabilities", pool.get_router_capabilities())

    @sio.on("sfu_create_transport")
    def handle_create_transport(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        direction = data.get("direction", "sendrecv")

        if not room_code:
            emit("sfu_error", {"message": "Room code required"})
            return

        router = get_or_create_sfu_router(room_code)
        transport = router.create_web_rtc_transport(direction=direction)

        emit("sfu_transport_created", transport.get_transport_options())
        log.debug("Created SFU transport %s for SID %s in room %s", transport.id, sid, room_code)

    @sio.on("sfu_connect_transport")
    def handle_connect_transport(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        transport_id = data.get("transport_id")
        dtls_parameters = data.get("dtlsParameters", {})

        if not room_code or not transport_id:
            emit("sfu_error", {"message": "Transport ID & Room code required"})
            return

        router = get_or_create_sfu_router(room_code)
        transport = router.transports.get(transport_id)

        if not transport:
            emit("sfu_error", {"message": f"Transport {transport_id} not found"})
            return

        res = transport.connect(dtls_parameters)
        emit("sfu_transport_connected", res)

    @sio.on("sfu_produce")
    def handle_produce(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        transport_id = data.get("transport_id")
        kind = data.get("kind", "audio")
        rtp_parameters = data.get("rtpParameters", {})

        if not room_code or not transport_id:
            emit("sfu_error", {"message": "Missing transport_id or room_code"})
            return

        router = get_or_create_sfu_router(room_code)
        try:
            app_data = {"peer_sid": sid, "user_id": info.get("user_id"), "display_name": info.get("display_name")}
            producer = router.create_producer(
                transport_id=transport_id,
                kind=kind,
                rtp_parameters=rtp_parameters,
                app_data=app_data
            )
            emit("sfu_produced", {"producer_id": producer.id, "kind": kind})

            # Broadcast new producer announcement to other peers in room
            sio.emit("sfu_new_producer", {
                "producer_id": producer.id,
                "producer_sid": sid,
                "producer_name": info.get("display_name", "Peer"),
                "kind": kind
            }, to=room_code, include_self=False)

        except Exception as e:
            log.error("SFU produce error: %s", e)
            emit("sfu_error", {"message": str(e)})

    @sio.on("sfu_consume")
    def handle_consume(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        producer_id = data.get("producer_id")
        transport_id = data.get("transport_id")
        rtp_parameters = data.get("rtpParameters", {})

        if not room_code or not producer_id or not transport_id:
            emit("sfu_error", {"message": "Missing producer_id or transport_id"})
            return

        router = get_or_create_sfu_router(room_code)
        try:
            consumer = router.create_consumer(
                producer_id=producer_id,
                transport_id=transport_id,
                rtp_parameters=rtp_parameters,
                app_data={"subscriber_sid": sid}
            )
            emit("sfu_consumed", consumer.get_stats())
        except Exception as e:
            log.error("SFU consume error: %s", e)
            emit("sfu_error", {"message": str(e)})

    @sio.on("sfu_set_preferred_layers")
    def handle_set_layers(data):
        room_code = data.get("room_code")
        consumer_id = data.get("consumer_id")
        spatial_layer = data.get("spatial_layer", 2)

        if not room_code or not consumer_id:
            return

        router = get_or_create_sfu_router(room_code)
        consumer = router.consumers.get(consumer_id)
        if consumer:
            consumer.set_preferred_layers(spatial_layer)
            emit("sfu_layers_changed", {"consumer_id": consumer_id, "spatial_layer": consumer.current_spatial_layer})

    @sio.on("sfu_vad_energy")
    def handle_vad_energy(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        dbfs = data.get("audio_level_dbfs", -100.0)

        if not room_code:
            return

        router = get_or_create_sfu_router(room_code)
        event = router.process_vad_energy(
            sid=sid,
            display_name=info.get("display_name", "Peer"),
            user_id=info.get("user_id"),
            dbfs=dbfs
        )

        if event and event.is_speaking:
            sio.emit("sfu_active_speaker_change", event.to_dict(), to=room_code)

    @sio.on("sfu_get_stats")
    def handle_get_stats(data):
        room_code = data.get("room_code")
        if not room_code:
            return
        router = get_or_create_sfu_router(room_code)
        emit("sfu_stats_response", router.get_stats())
