"""
ElevateIQ — Real-Time Vector Whiteboard Socket.IO Handlers
==========================================================
Events:
  - whiteboard_draw_event  → Relay vector draw strokes to room participants
  - whiteboard_clear       → Broadcast canvas clear event
  - whiteboard_save_state  → Persist snapshot to database
  - whiteboard_get_state   → Retrieve canvas snapshot for joining participant
"""

import logging
from flask import request
from flask_socketio import emit
from backend.extensions import db
from backend.models.models import WhiteboardSnapshot
from backend.sockets.connection import ACTIVE_SOCKETS

log = logging.getLogger("elevateiq.sockets.whiteboard")


def register_whiteboard_handlers(sio):

    @sio.on("whiteboard_draw_event")
    def handle_draw_event(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")

        if not room_code:
            return

        sio.emit("whiteboard_draw_event", {
            "sender_sid": sid,
            "sender_name": info.get("display_name", "User"),
            "stroke": data.get("stroke"),
        }, to=room_code, include_self=False)

    @sio.on("whiteboard_clear")
    def handle_clear(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")

        if not room_code:
            return

        sio.emit("whiteboard_cleared", {
            "sender_sid": sid,
        }, to=room_code, include_self=False)

    @sio.on("whiteboard_save_state")
    def handle_save_state(data):
        room_code = data.get("room_code")
        snapshot_json = data.get("snapshot_json")

        if not room_code or snapshot_json is None:
            return

        snapshot = WhiteboardSnapshot.query.filter_by(meeting_code=room_code).first()
        if not snapshot:
            snapshot = WhiteboardSnapshot(meeting_code=room_code, snapshot_json=snapshot_json)
            db.session.add(snapshot)
        else:
            snapshot.snapshot_json = snapshot_json

        db.session.commit()
        log.debug("Saved whiteboard snapshot for meeting %s", room_code)

    @sio.on("whiteboard_get_state")
    def handle_get_state(data):
        room_code = data.get("room_code")
        if not room_code:
            return

        snapshot = WhiteboardSnapshot.query.filter_by(meeting_code=room_code).first()
        if snapshot:
            emit("whiteboard_state_response", snapshot.to_dict())
        else:
            emit("whiteboard_state_response", {"snapshot_json": []})
