"""
ElevateIQ — Socket.IO WebRTC Signaling Handlers
================================================
Events:
  - webrtc_offer          → Relay SDP offer to target peer SID
  - webrtc_answer         → Relay SDP answer to target peer SID
  - webrtc_ice_candidate  → Relay ICE candidate to target peer SID
  - media_state_change    → Broadcast audio/video/screen state updates to room
"""

import logging
from flask import request
from flask_socketio import emit
from backend.sockets.connection import ACTIVE_SOCKETS

log = logging.getLogger("elevateiq.sockets.signaling")


def register_signaling_handlers(sio):

    @sio.on("webrtc_offer")
    def handle_offer(data):
        sid = request.sid
        target_sid = data.get("target_sid")
        sdp = data.get("sdp")

        if not target_sid or not sdp:
            return

        sender_info = ACTIVE_SOCKETS.get(sid, {})

        sio.emit("webrtc_offer", {
            "sender_sid": sid,
            "sender_user_id": sender_info.get("user_id"),
            "sender_name": sender_info.get("display_name", "Peer"),
            "sdp": sdp,
        }, room=target_sid)

        log.debug("Relayed WebRTC offer from %s to %s", sid, target_sid)

    @sio.on("webrtc_answer")
    def handle_answer(data):
        sid = request.sid
        target_sid = data.get("target_sid")
        sdp = data.get("sdp")

        if not target_sid or not sdp:
            return

        sio.emit("webrtc_answer", {
            "sender_sid": sid,
            "sdp": sdp,
        }, room=target_sid)

        log.debug("Relayed WebRTC answer from %s to %s", sid, target_sid)

    @sio.on("webrtc_ice_candidate")
    def handle_ice_candidate(data):
        sid = request.sid
        target_sid = data.get("target_sid")
        candidate = data.get("candidate")

        if not target_sid or not candidate:
            return

        sio.emit("webrtc_ice_candidate", {
            "sender_sid": sid,
            "candidate": candidate,
        }, room=target_sid)

        log.debug("Relayed ICE candidate from %s to %s", sid, target_sid)

    @sio.on("media_state_change")
    def handle_media_state(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")

        if not room_code:
            return

        payload = {
            "sid": sid,
            "user_id": info.get("user_id"),
            "is_audio_muted": data.get("is_audio_muted", False),
            "is_video_off": data.get("is_video_off", False),
            "is_screen_sharing": data.get("is_screen_sharing", False),
            "hand_raised": data.get("hand_raised", False),
        }

        sio.emit("media_state_changed", payload, to=room_code, include_self=False)
        log.debug("Media state changed for %s in room %s", sid, room_code)
