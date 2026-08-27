"""
ElevateIQ — Breakout Rooms Management REST APIs
================================================
API Endpoints:
  - POST /api/breakout/create           → Create dynamic breakout rooms
  - POST /api/breakout/assign           → Assign participants to rooms
  - POST /api/breakout/close            → Close all breakout rooms & return to main call
  - GET  /api/breakout/meeting/<code >    → Get active breakout rooms for meeting
"""

import logging
import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import BreakoutRoom, BreakoutAssignment, MeetingParticipant, Meeting

breakout_bp = Blueprint("breakout", __name__, url_prefix="/api/breakout")
log = logging.getLogger("elevateiq.breakout")


@breakout_bp.route("/create", methods=["POST"])
@jwt_required()
def create_breakout_rooms():
    """Create dynamic breakout rooms for a meeting."""
    data = request.get_json() or {}
    meeting_code = data.get("meeting_code")
    num_rooms = data.get("num_rooms", 2)
    duration_minutes = data.get("duration_minutes", 15)
    auto_assign = data.get("auto_assign", True)

    if not meeting_code or num_rooms < 1:
        return jsonify({"error": "meeting_code and num_rooms >= 1 required"}), 400

    # Close existing active breakout rooms for this meeting
    existing = BreakoutRoom.query.filter_by(meeting_code=meeting_code, is_active=True).all()
    for room in existing:
        room.is_active = False

    created_rooms = []
    for i in range(1, num_rooms + 1):
        room = BreakoutRoom(
            meeting_code=meeting_code,
            room_name=f"Breakout Room {i}",
            duration_minutes=duration_minutes,
            is_active=True
        )
        db.session.add(room)
        created_rooms.append(room)

    db.session.flush()

    # Auto-assign active meeting participants if requested
    if auto_assign:
        meeting = Meeting.query.filter_by(meeting_code=meeting_code).first()
        if meeting:
            participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
            user_ids = [p.user_id for p in participants if p.user_id]
            random.shuffle(user_ids)

            for idx, u_id in enumerate(user_ids):
                assigned_room = created_rooms[idx % len(created_rooms)]
                assignment = BreakoutAssignment(room_id=assigned_room.id, user_id=u_id)
                db.session.add(assignment)

    db.session.commit()
    log.info("Created %d breakout rooms for meeting %s", len(created_rooms), meeting_code)
    return jsonify([r.to_dict() for r in created_rooms]), 201


@breakout_bp.route("/meeting/<string:meeting_code>", methods=["GET"])
@jwt_required()
def get_breakout_rooms(meeting_code):
    """Get active breakout rooms for a meeting."""
    rooms = BreakoutRoom.query.filter_by(meeting_code=meeting_code, is_active=True).all()
    return jsonify([r.to_dict() for r in rooms]), 200


@breakout_bp.route("/assign", methods=["POST"])
@jwt_required()
def assign_participant():
    """Assign or move a participant to a specific breakout room."""
    data = request.get_json() or {}
    room_id = data.get("room_id")
    user_id = data.get("user_id")

    if not room_id or not user_id:
        return jsonify({"error": "room_id and user_id required"}), 400

    room = BreakoutRoom.query.get(room_id)
    if not room or not room.is_active:
        return jsonify({"error": "Active breakout room not found"}), 404

    # Clear existing breakout assignment for user in this meeting
    active_rooms = BreakoutRoom.query.filter_by(meeting_code=room.meeting_code, is_active=True).all()
    room_ids = [r.id for r in active_rooms]
    BreakoutAssignment.query.filter(BreakoutAssignment.room_id.in_(room_ids), BreakoutAssignment.user_id == user_id).delete(synchronize_session=False)

    assignment = BreakoutAssignment(room_id=room_id, user_id=user_id)
    db.session.add(assignment)
    db.session.commit()

    return jsonify(room.to_dict()), 200


@breakout_bp.route("/close", methods=["POST"])
@jwt_required()
def close_breakout_rooms():
    """Close all active breakout rooms for a meeting."""
    data = request.get_json() or {}
    meeting_code = data.get("meeting_code")

    if not meeting_code:
        return jsonify({"error": "meeting_code is required"}), 400

    rooms = BreakoutRoom.query.filter_by(meeting_code=meeting_code, is_active=True).all()
    for room in rooms:
        room.is_active = False

    db.session.commit()
    log.info("Closed breakout rooms for meeting %s", meeting_code)
    return jsonify({"message": "Breakout rooms closed successfully"}), 200
