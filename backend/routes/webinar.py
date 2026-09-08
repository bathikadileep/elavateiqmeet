"""
ElevateIQ — Webinar & Event REST API Endpoints
==============================================
API Endpoints:
  - POST /api/webinar/qa/ask           → Ask Q&A question
  - POST /api/webinar/qa/upvote        → Upvote question
  - POST /api/webinar/qa/approve       → Approve / answer question (Host/Co-host)
  - POST /api/webinar/stage/promote    → Promote attendee to stage
  - POST /api/webinar/hand/raise       → Raise hand in priority queue
  - POST /api/webinar/breakout/create  → Split room into breakout sub-rooms
  - POST /api/webinar/rtmp/start       → Start RTMP broadcast push stream
"""

import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.webinar_service import get_webinar_service
from backend.services.breakout_service import BreakoutService
from backend.services.rtmp_egress import get_rtmp_service

webinar_bp = Blueprint("webinar", __name__, url_prefix="/api/webinar")
log = logging.getLogger("elevateiq.webinar")


@webinar_bp.route("/qa/ask", methods=["POST"])
@jwt_required()
def ask_question():
    """Submit Q&A question in a webinar."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    room_code = data.get("room_code", "").strip()
    question = data.get("question", "").strip()
    speaker_name = data.get("speaker_name", "Attendee")

    if not room_code or not question:
        return jsonify({"error": "room_code and question parameters are required"}), 400

    service = get_webinar_service()
    res = service.ask_question(room_code, current_user_id, speaker_name, question)
    return jsonify(res), 201


@webinar_bp.route("/qa/upvote", methods=["POST"])
@jwt_required()
def upvote_question():
    """Upvote Q&A question."""
    data = request.get_json() or {}
    room_code = data.get("room_code", "").strip()
    question_id = data.get("question_id", "").strip()

    service = get_webinar_service()
    res = service.upvote_question(room_code, question_id)
    if not res:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(res), 200


@webinar_bp.route("/hand/raise", methods=["POST"])
@jwt_required()
def raise_hand():
    """Raise hand in webinar audience."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    room_code = data.get("room_code", "").strip()
    speaker_name = data.get("speaker_name", "Attendee")

    service = get_webinar_service()
    res = service.raise_hand(room_code, current_user_id, speaker_name)
    return jsonify(res), 200


@webinar_bp.route("/breakout/create", methods=["POST"])
@jwt_required()
def create_breakout():
    """Create breakout sub-rooms."""
    data = request.get_json() or {}
    main_room_code = data.get("main_room_code", "").strip()
    participants = data.get("participants", [])
    num_rooms = data.get("num_rooms", 2)
    duration = data.get("duration_minutes", 15)

    res = BreakoutService.create_breakout_rooms(main_room_code, participants, num_rooms, duration)
    return jsonify(res), 201


@webinar_bp.route("/rtmp/start", methods=["POST"])
@jwt_required()
def start_rtmp():
    """Start RTMP stream egress."""
    data = request.get_json() or {}
    room_code = data.get("room_code", "").strip()
    rtmp_url = data.get("rtmp_url", "").strip()
    stream_key = data.get("stream_key", "").strip()

    if not room_code or not rtmp_url or not stream_key:
        return jsonify({"error": "room_code, rtmp_url, and stream_key are required"}), 400

    service = get_rtmp_service()
    res = service.start_rtmp_stream(room_code, rtmp_url, stream_key)
    return jsonify(res), 200
