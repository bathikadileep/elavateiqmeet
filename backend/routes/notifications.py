"""
ElevateIQ — Notifications Blueprint
=====================================
Endpoints:
  GET /api/v1/notifications               → List user notifications (unread count & list)
  PUT /api/v1/notifications/<id>/read     → Mark single notification as read
  PUT /api/v1/notifications/read-all      → Mark all user notifications as read
  POST /api/v1/notifications/send         → Dispatch meeting reminders, chat alerts, attendance alerts
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import Notification, User
from backend.services.notification_service import create_and_dispatch_notification
from backend.core.errors import (
    BadRequestError,
    NotFoundError,
)

log = logging.getLogger("elevateiq.notifications")

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")


# ── 1. List Notifications Endpoint ───────────────────────────────────────────

@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    """
    GET /api/v1/notifications
    Returns list of notifications and total unread count for current user.
    """
    user_id = get_jwt_identity()

    notifications = db.session.scalars(
        db.select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(30)
    ).all()

    unread_count = db.session.scalar(
        db.select(db.func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ) or 0

    return jsonify({
        "unread_count": unread_count,
        "notifications": [n.to_dict() for n in notifications],
    }), 200


# ── 2. Mark Single Notification as Read ───────────────────────────────────────

@notifications_bp.route("/<notif_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notif_id):
    """
    PUT /api/v1/notifications/<notif_id>/read
    """
    user_id = get_jwt_identity()
    notif = db.session.get(Notification, notif_id)

    if not notif or notif.user_id != user_id:
        raise NotFoundError("Notification not found.")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"message": "Notification marked as read."}), 200


# ── 3. Mark All Notifications as Read ─────────────────────────────────────────

@notifications_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    """
    PUT /api/v1/notifications/read-all
    """
    user_id = get_jwt_identity()

    db.session.execute(
        db.update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    db.session.commit()

    return jsonify({"message": "All notifications marked as read."}), 200


# ── 4. Send Notification Dispatch Trigger ─────────────────────────────────────

@notifications_bp.route("/send", methods=["POST"])
@jwt_required()
def send_notification_trigger():
    """
    POST /api/v1/notifications/send
    Body: { recipient_id, notif_type, title, body, send_email? }
    Triggers meeting reminders, chat alerts, attendance alerts, system alerts.
    """
    data = request.get_json(silent=True) or {}

    recipient_id = data.get("recipient_id")
    notif_type   = data.get("notif_type", "system_alert")
    title        = data.get("title")
    body         = data.get("body")
    send_email   = data.get("send_email", False)

    if not recipient_id or not title:
        raise BadRequestError("recipient_id and title are required.")

    notif = create_and_dispatch_notification(
        user_id=recipient_id,
        notif_type=notif_type,
        title=title,
        body=body,
        send_email=send_email,
    )

    if not notif:
        raise BadRequestError("Could not send notification.")

    return jsonify({
        "message": "Notification dispatched successfully.",
        "notification": notif.to_dict(),
    }), 201
