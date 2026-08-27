"""
ElevateIQ — Notification Dispatch Service
============================================
Creates DB notifications, emits real-time Socket.IO alerts,
and triggers background email notifications.
"""

import logging
from datetime import datetime, timezone
from backend.extensions import db, socketio
from backend.models.models import Notification, User
from backend.services.email_service import send_email_async, send_meeting_reminder_email

log = logging.getLogger("elevateiq.services.notifications")


def create_and_dispatch_notification(
    user_id: str,
    notif_type: str,
    title: str,
    body: str = None,
    metadata: dict = None,
    send_email: bool = False,
):
    """
    Persists notification to DB, emits real-time Socket.IO alert, and sends email if enabled.
    """
    try:
        user = db.session.get(User, user_id)
        if not user or user.is_deleted:
            return None

        notif = Notification(
            user_id=user_id,
            type=notif_type,
            title=title,
            body=body,
            notif_metadata=metadata or {},
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(notif)
        db.session.commit()

        notif_dict = notif.to_dict()

        # Real-time Socket.IO broadcast to target user
        socketio.emit("new_notification", notif_dict, room=f"user_{user_id}")

        # Send email notification if user has valid email and send_email is True
        if send_email and user.email:
            send_email_async(
                recipient=user.email,
                subject=title,
                html_content=f"<h3>{title}</h3><p>{body or ''}</p>"
            )

        log.info("Dispatched notification '%s' to user_id=%s", title, user_id)
        return notif
    except Exception as exc:
        db.session.rollback()
        log.error("Failed to create & dispatch notification: %s", exc)
        return None
