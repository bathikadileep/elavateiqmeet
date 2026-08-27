"""
ElevateIQ — Socket.IO Real-Time Chat & Typing Handlers
======================================================
Events:
  - send_message        → Broadcast room chat or direct private message (DM)
  - typing_start        → Broadcast user typing indicator
  - typing_stop         → Clear user typing indicator
  - load_chat_history   → Fetch past messages for a room from Neon PostgreSQL
"""

import logging
from datetime import datetime, timezone
from flask import request
from flask_socketio import emit
from backend.extensions import db, socketio
from backend.models.models import Meeting, Message, User
from backend.sockets.connection import ACTIVE_SOCKETS

log = logging.getLogger("elevateiq.sockets.chat")


def register_chat_handlers(sio):

    @sio.on("send_message")
    def handle_send_message(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})

        room_code    = data.get("room_code") or info.get("room_code")
        content      = (data.get("content", "") or "").strip()
        recipient_id = data.get("recipient_id")  # None = public room chat, string = private DM
        sender_id    = data.get("user_id") or info.get("user_id")
        sender_name  = data.get("display_name") or info.get("display_name", "Anonymous")

        if not content or not room_code:
            return

        now_iso = datetime.now(timezone.utc).isoformat() + "Z"

        msg_payload = {
            "id": f"msg-{datetime.now(timezone.utc).timestamp()}",
            "room_code": room_code,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "content": content,
            "is_private": bool(recipient_id),
            "recipient_id": recipient_id,
            "timestamp": now_iso,
        }

        # Save to database if meeting room exists
        try:
            meeting = db.session.execute(
                db.select(Meeting).filter_by(meeting_code=room_code, is_deleted=False)
            ).scalar_one_or_none()

            if meeting:
                db_msg = Message(
                    meeting_id=meeting.id,
                    user_id=sender_id,
                    message_type="text",
                    content=content,
                )
                db.session.add(db_msg)
                db.session.commit()
                msg_payload["id"] = db_msg.id
        except Exception as exc:
            db.session.rollback()
            log.warning("Could not persist chat message to DB: %s", exc)

        # Dispatch Message
        if recipient_id:
            # Private Chat (DM) → find target recipient socket SID
            target_sid = None
            for client_sid, client_info in ACTIVE_SOCKETS.items():
                if str(client_info.get("user_id")) == str(recipient_id):
                    target_sid = client_sid
                    break

            if target_sid:
                # Deliver to recipient
                sio.emit("new_message", msg_payload, room=target_sid)
                # Echo back to sender
                sio.emit("new_message", msg_payload, room=sid)
                log.info("Private message sent from %s to user_id=%s", sender_name, recipient_id)
            else:
                emit("error", {"message": "Recipient is no longer active in this room."})
        else:
            # Public Meeting Chat → Broadcast to all in room
            sio.emit("new_message", msg_payload, to=room_code)
            log.info("Public message sent in room %s by %s", room_code, sender_name)

    @sio.on("typing_start")
    def handle_typing_start(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        recipient_id = data.get("recipient_id")

        if not room_code:
            return

        payload = {
            "user_id": data.get("user_id") or info.get("user_id"),
            "display_name": data.get("display_name") or info.get("display_name", "Someone"),
            "recipient_id": recipient_id,
        }

        if recipient_id:
            target_sid = next(
                (c_sid for c_sid, c_info in ACTIVE_SOCKETS.items() if str(c_info.get("user_id")) == str(recipient_id)),
                None
            )
            if target_sid:
                sio.emit("user_typing", payload, room=target_sid)
        else:
            sio.emit("user_typing", payload, to=room_code, include_self=False)

    @sio.on("typing_stop")
    def handle_typing_stop(data):
        sid = request.sid
        info = ACTIVE_SOCKETS.get(sid, {})
        room_code = data.get("room_code") or info.get("room_code")
        recipient_id = data.get("recipient_id")

        if not room_code:
            return

        payload = {
            "user_id": data.get("user_id") or info.get("user_id"),
            "recipient_id": recipient_id,
        }

        if recipient_id:
            target_sid = next(
                (c_sid for c_sid, c_info in ACTIVE_SOCKETS.items() if str(c_info.get("user_id")) == str(recipient_id)),
                None
            )
            if target_sid:
                sio.emit("user_stopped_typing", payload, room=target_sid)
        else:
            sio.emit("user_stopped_typing", payload, to=room_code, include_self=False)

    @sio.on("load_chat_history")
    def handle_load_history(data):
        sid = request.sid
        room_code = data.get("room_code")
        if not room_code:
            return

        try:
            meeting = db.session.execute(
                db.select(Meeting).filter_by(meeting_code=room_code, is_deleted=False)
            ).scalar_one_or_none()

            if meeting:
                messages = db.session.scalars(
                    db.select(Message).where(
                        Message.meeting_id == meeting.id,
                        Message.is_deleted == False
                    ).order_by(Message.created_at.asc()).limit(50)
                ).all()

                history = [m.to_dict() for m in messages]
                emit("chat_history", {"room_code": room_code, "messages": history})
        except Exception as exc:
            log.warning("Could not load chat history: %s", exc)
