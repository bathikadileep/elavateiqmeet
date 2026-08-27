"""
ElevateIQ — Meeting Management Blueprint
===========================================
Endpoints:
  POST   /api/v1/meetings              → Create instant or scheduled meeting
  GET    /api/v1/meetings              → List user meetings (scheduled/live)
  GET    /api/v1/meetings/code/<code>   → Get meeting by code
  GET    /api/v1/meetings/history      → Meeting attendance & hosted history
  GET    /api/v1/meetings/<id>         → Get meeting details
  PUT    /api/v1/meetings/<id>         → Update scheduled meeting
  DELETE /api/v1/meetings/<id>         → Soft delete meeting
  POST   /api/v1/meetings/<id>/invite  → Invite participants by email/username
"""

import re
import secrets
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import (
    Meeting,
    MeetingParticipant,
    Notification,
    User,
)
from backend.core.errors import (
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
)

log = logging.getLogger("elevateiq.meetings")

meetings_bp = Blueprint("meetings", __name__, url_prefix="/api/v1/meetings")


def _generate_meeting_code() -> str:
    """Generate a clean 10-char alphanumeric meeting code: xxx-xxxx-xxx."""
    part1 = secrets.token_hex(2)[:3]
    part2 = secrets.token_hex(2)
    part3 = secrets.token_hex(2)[:3]
    return f"{part1}-{part2}-{part3}"


# ── 1. Create Meeting ─────────────────────────────────────────────────────────

@meetings_bp.route("", methods=["POST"])
@jwt_required()
def create_meeting():
    """
    POST /api/v1/meetings
    Body: { title?, description?, meeting_type?, scheduled_start?, scheduled_end?, max_participants?, password? }
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    title            = (data.get("title", "") or "").strip() or "Untitled Meeting"
    description      = (data.get("description", "") or "").strip()
    meeting_type     = data.get("meeting_type", "instant")
    max_participants = int(data.get("max_participants", 50))
    password         = data.get("password", "") or ""

    if meeting_type not in ["instant", "scheduled", "recurring"]:
        raise BadRequestError("Invalid meeting_type. Must be instant, scheduled, or recurring.")

    if not (2 <= max_participants <= 500):
        raise BadRequestError("max_participants must be between 2 and 500.")

    scheduled_start = None
    scheduled_end   = None

    if meeting_type == "scheduled":
        start_str = data.get("scheduled_start")
        end_str   = data.get("scheduled_end")
        if start_str:
            try:
                scheduled_start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            except ValueError:
                raise BadRequestError("Invalid scheduled_start ISO timestamp format.")

        if end_str:
            try:
                scheduled_end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            except ValueError:
                raise BadRequestError("Invalid scheduled_end ISO timestamp format.")

    # Generate unique code
    code = _generate_meeting_code()

    meeting = Meeting(
        meeting_code=code,
        title=title,
        description=description,
        host_id=user_id,
        status="scheduled" if meeting_type == "scheduled" else "live",
        meeting_type=meeting_type,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        actual_start=datetime.now(timezone.utc) if meeting_type == "instant" else None,
        max_participants=max_participants,
    )

    if password:
        from backend.extensions import bcrypt
        meeting.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    db.session.add(meeting)
    db.session.flush()

    # Automatically add host as participant with role 'host'
    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=user_id,
        role="host",
        status="joined" if meeting_type == "instant" else "invited",
    )
    db.session.add(participant)
    db.session.commit()

    log.info("Meeting created: %s (%s) by user_id=%s", meeting.title, code, user_id)
    return jsonify({
        "message": "Meeting created successfully.",
        "meeting": meeting.to_dict(),
    }), 201


# ── 2. List Meetings ──────────────────────────────────────────────────────────

@meetings_bp.route("", methods=["GET"])
@jwt_required()
def list_meetings():
    """
    GET /api/v1/meetings?status=scheduled|live|ended
    Returns user's hosted and joined meetings.
    """
    user_id = get_jwt_identity()
    status_filter = request.args.get("status")

    query = db.select(Meeting).where(
        Meeting.is_deleted == False,
        db.or_(
            Meeting.host_id == user_id,
            Meeting.id.in_(
                db.select(MeetingParticipant.meeting_id).where(MeetingParticipant.user_id == user_id)
            )
        )
    )

    if status_filter:
        query = query.where(Meeting.status == status_filter)

    query = query.order_by(Meeting.created_at.desc())
    meetings = db.session.scalars(query).all()

    return jsonify({"meetings": [m.to_dict() for m in meetings]}), 200


# ── 3. Get Meeting By Code ────────────────────────────────────────────────────

@meetings_bp.route("/code/<code>", methods=["GET"])
@jwt_required()
def get_by_code(code):
    """
    GET /api/v1/meetings/code/<code>
    Look up room details before joining.
    """
    meeting = db.session.execute(
        db.select(Meeting).where(
            Meeting.meeting_code == code,
            Meeting.is_deleted == False
        )
    ).scalar_one_or_none()

    if not meeting:
        raise NotFoundError("Meeting room not found or code is invalid.")

    return jsonify({"meeting": meeting.to_dict()}), 200


# ── 4. Meeting History ────────────────────────────────────────────────────────

@meetings_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    """
    GET /api/v1/meetings/history
    """
    user_id = get_jwt_identity()

    query = db.select(Meeting).where(
        Meeting.is_deleted == False,
        db.or_(
            Meeting.host_id == user_id,
            Meeting.id.in_(
                db.select(MeetingParticipant.meeting_id).where(MeetingParticipant.user_id == user_id)
            )
        )
    ).order_by(Meeting.created_at.desc())

    meetings = db.session.scalars(query).all()
    history = []
    for m in meetings:
        item = m.to_dict()
        item["is_host"] = (m.host_id == user_id)
        history.append(item)

    return jsonify({"meetings": history}), 200


# ── 5. Get Meeting Details ────────────────────────────────────────────────────

@meetings_bp.route("/<meeting_id>", methods=["GET"])
@jwt_required()
def get_meeting(meeting_id):
    """
    GET /api/v1/meetings/<meeting_id>
    """
    meeting = db.session.get(Meeting, meeting_id)
    if not meeting or meeting.is_deleted:
        raise NotFoundError("Meeting not found.")

    return jsonify({"meeting": meeting.to_dict()}), 200


# ── 6. Update Meeting ─────────────────────────────────────────────────────────

@meetings_bp.route("/<meeting_id>", methods=["PUT"])
@jwt_required()
def update_meeting(meeting_id):
    """
    PUT /api/v1/meetings/<meeting_id>
    Body: { title?, description?, scheduled_start?, scheduled_end?, max_participants? }
    """
    user_id = get_jwt_identity()
    meeting = db.session.get(Meeting, meeting_id)

    if not meeting or meeting.is_deleted:
        raise NotFoundError("Meeting not found.")

    if meeting.host_id != user_id:
        raise AuthorizationError("Only the meeting host can edit meeting details.")

    data = request.get_json(silent=True) or {}

    if "title" in data:
        meeting.title = (data["title"] or "").strip() or meeting.title
    if "description" in data:
        meeting.description = (data["description"] or "").strip()
    if "max_participants" in data:
        meeting.max_participants = int(data["max_participants"])

    db.session.commit()
    log.info("Meeting updated: %s", meeting.id)

    return jsonify({"message": "Meeting updated successfully.", "meeting": meeting.to_dict()}), 200


# ── 7. Delete Meeting ─────────────────────────────────────────────────────────

@meetings_bp.route("/<meeting_id>", methods=["DELETE"])
@jwt_required()
def delete_meeting(meeting_id):
    """
    DELETE /api/v1/meetings/<meeting_id>
    Soft deletes meeting. Host or super_admin permission required.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    meeting = db.session.get(Meeting, meeting_id)

    if not meeting or meeting.is_deleted:
        raise NotFoundError("Meeting not found.")

    is_host = (meeting.host_id == user_id)
    is_admin = user and user.roles and any(r.name == "super_admin" for r in user.roles)

    if not is_host and not is_admin:
        raise AuthorizationError("Only the meeting host or platform administrator can delete this meeting.")

    meeting.is_deleted = True
    meeting.deleted_at = datetime.now(timezone.utc)
    meeting.status = "cancelled"
    db.session.commit()

    log.info("Meeting deleted: %s", meeting.id)
    return jsonify({"message": "Meeting deleted successfully."}), 200


# ── 8. Invite Participants ─────────────────────────────────────────────────────

@meetings_bp.route("/<meeting_id>/invite", methods=["POST"])
@jwt_required()
def invite_participants(meeting_id):
    """
    POST /api/v1/meetings/<meeting_id>/invite
    Body: { emails: [string], usernames: [string] }
    """
    user_id = get_jwt_identity()
    host_user = db.session.get(User, user_id)
    meeting = db.session.get(Meeting, meeting_id)

    if not meeting or meeting.is_deleted:
        raise NotFoundError("Meeting not found.")

    data = request.get_json(silent=True) or {}
    emails = data.get("emails", [])
    usernames = data.get("usernames", [])

    invited_users = []

    # Process emails & usernames
    for email in emails:
        user = db.session.execute(
            db.select(User).filter_by(email=email.strip().lower(), is_deleted=False)
        ).scalar_one_or_none()
        if user and user not in invited_users:
            invited_users.append(user)

    for username in usernames:
        user = db.session.execute(
            db.select(User).filter_by(username=username.strip(), is_deleted=False)
        ).scalar_one_or_none()
        if user and user not in invited_users:
            invited_users.append(user)

    invitations_sent = 0
    for target in invited_users:
        # Create participant entry if not exists
        existing = db.session.execute(
            db.select(MeetingParticipant).filter_by(meeting_id=meeting.id, user_id=target.id)
        ).scalar_one_or_none()

        if not existing:
            mp = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=target.id,
                role="participant",
                status="invited",
            )
            db.session.add(mp)

        # Create notification for invited user
        notif = Notification(
            user_id=target.id,
            type="meeting_invite",
            title=f"Invitation: {meeting.title}",
            body=f"{host_user.display_name or host_user.username} invited you to join meeting '{meeting.title}' (Code: {meeting.meeting_code}).",
            reference_id=meeting.id,
        )
        db.session.add(notif)
        invitations_sent += 1

    db.session.commit()
    log.info("Sent %d invitations for meeting: %s", invitations_sent, meeting.meeting_code)

    return jsonify({
        "message": f"Successfully sent {invitations_sent} invitations.",
        "invited_count": invitations_sent,
        "meeting_code": meeting.meeting_code,
        "join_url": f"/room/{meeting.meeting_code}",
    }), 200
