"""
ElevateIQ — Live Speech Captioning Socket.IO Handlers
=====================================================
Events:
  - speech_transcript_event  → Relay live subtitle lines across room participants
"""

import logging
from flask import request
from backend.sockets.connection import ACTIVE_SOCKETS

log = logging.getLogger("elevateiq.sockets.captions")


def register_caption_handlers(sio):

    @sio.on("speech_transcript_event")
    def handle_speech_transcript(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")

        if not room_code:
            return

        sio.emit("speech_transcript_event", {
            "sender_sid": sid,
            "speaker_name": data.get("speaker_name") or info.get("display_name", "Speaker"),
            "text": data.get("text", ""),
            "is_final": data.get("is_final", False),
            "timestamp": data.get("timestamp"),
        }, to=room_code, include_self=False)
