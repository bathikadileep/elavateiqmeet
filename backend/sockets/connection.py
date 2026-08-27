"""
ElevateIQ — Socket.IO Connection & Room Management Handlers
============================================================
Events:
  - connect        → Handle connection authorization & track socket
  - join_room      → Join meeting room, update DB roster, broadcast join notification
  - leave_room     → Leave meeting room, broadcast leave notification
  - disconnect     → Handle socket disconnection
"""

import logging
from flask import request
from flask_socketio import join_room as flask_join_room, leave_room as flask_leave_room, emit
from backend.extensions import db, socketio
from backend.models.models import Meeting, MeetingParticipant, User

log = logging.getLogger("elevateiq.sockets.connection")

# In-memory mapping of active socket_id → { user_id, username, display_name, room_code }
ACTIVE_SOCKETS = {}


def register_connection_handlers(sio):

    @sio.on("connect")
    def handle_connect():
        sid = request.sid
        log.info("Socket connected: sid=%s", sid)
        emit("connected", {"sid": sid, "status": "ok"})

    @sio.on("join_room")
    def handle_join_room(data):
        sid = request.sid
        room_code    = (data.get("room_code", "") or "").strip()
        user_id      = data.get("user_id")
        username     = data.get("username", "Guest")
        display_name = data.get("display_name", username)

        if not room_code:
            emit("error", {"message": "room_code is required to join."})
            return

        # Join Flask-SocketIO room
        flask_join_room(room_code)

        # Store in active memory cache
        ACTIVE_SOCKETS[sid] = {
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "room_code": room_code,
            "sid": sid,
        }

        # Update DB participant socket_id if authenticated user
        if user_id:
            try:
                meeting = db.session.execute(
                    db.select(Meeting).filter_by(meeting_code=room_code, is_deleted=False)
                ).scalar_one_or_none()

                if meeting:
                    mp = db.session.execute(
                        db.select(MeetingParticipant).filter_by(meeting_id=meeting.id, user_id=user_id)
                    ).scalar_one_or_none()

                    if not mp:
                        mp = MeetingParticipant(
                            meeting_id=meeting.id,
                            user_id=user_id,
                            socket_id=sid,
                            role="participant",
                            status="joined",
                        )
                        db.session.add(mp)
                    else:
                        mp.socket_id = sid
                        mp.status = "joined"

                    db.session.commit()
            except Exception as exc:
                db.session.rollback()
                log.warning("Could not update participant socket in DB: %s", exc)

        log.info("User %s (%s) joined room: %s", display_name, sid, room_code)

        # 1. Notify room about new user join (Join Notification)
        emit("user_joined", {
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "sid": sid,
            "timestamp": data.get("timestamp"),
        }, to=room_code)

        # 2. Broadcast updated online roster to all users in room
        _broadcast_room_roster(room_code)

    @sio.on("leave_room")
    def handle_leave_room(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.pop(sid, None)

        if info:
            room_code = info["room_code"]
            flask_leave_room(room_code)

            log.info("User %s left room: %s", info["display_name"], room_code)

            # Broadcast leave notification
            emit("user_left", {
                "user_id": info["user_id"],
                "username": info["username"],
                "display_name": info["display_name"],
                "sid": sid,
            }, to=room_code)

            _broadcast_room_roster(room_code)

    @sio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        info = ACTIVE_SOCKETS.pop(sid, None)

        if info:
            room_code = info["room_code"]
            flask_leave_room(room_code)

            log.info("Socket disconnected: sid=%s from room=%s", sid, room_code)

            emit("user_left", {
                "user_id": info["user_id"],
                "username": info["username"],
                "display_name": info["display_name"],
                "sid": sid,
            }, to=room_code)

            _broadcast_room_roster(room_code)


def _broadcast_room_roster(room_code: str):
    """Compile and emit active online roster for a room."""
    roster = [
        {
            "sid": item["sid"],
            "user_id": item["user_id"],
            "username": item["username"],
            "display_name": item["display_name"],
        }
        for item in ACTIVE_SOCKETS.values()
        if item["room_code"] == room_code
    ]
    socketio.emit("room_roster", {"room_code": room_code, "users": roster}, to=room_code)
