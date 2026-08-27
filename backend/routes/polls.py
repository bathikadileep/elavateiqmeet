"""
ElevateIQ — Live In-Meeting Polling REST APIs
==============================================
API Endpoints:
  - POST /api/polls                    → Create a new live poll
  - GET  /api/polls/meeting/<code >     → Get all polls for a meeting
  - POST /api/polls/<id >/vote          → Submit single or multi-choice vote
  - POST /api/polls/<id >/publish       → Publish poll results to meeting room
  - POST /api/polls/<id >/close         → Close poll for voting
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import Poll, PollOption, PollVote, User

polls_bp = Blueprint("polls", __name__, url_prefix="/api/polls")
log = logging.getLogger("elevateiq.polls")


@polls_bp.route("", methods=["POST"])
@jwt_required()
def create_poll():
    """Create a new poll for a meeting."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}

    meeting_code = data.get("meeting_code")
    question = data.get("question")
    options = data.get("options", [])
    is_multiselect = data.get("is_multiselect", False)

    if not meeting_code or not question or len(options) < 2:
        return jsonify({"error": "meeting_code, question, and at least 2 options are required"}), 400

    poll = Poll(
        meeting_code=meeting_code,
        created_by=current_user_id,
        question=question,
        is_multiselect=is_multiselect
    )
    db.session.add(poll)
    db.session.flush()

    for opt_text in options:
        if str(opt_text).strip():
            opt = PollOption(poll_id=poll.id, option_text=str(opt_text).strip())
            db.session.add(opt)

    db.session.commit()
    log.info("Created poll id=%s for meeting_code=%s", poll.id, meeting_code)
    return jsonify(poll.to_dict()), 201


@polls_bp.route("/meeting/<string:meeting_code>", methods=["GET"])
@jwt_required()
def list_polls(meeting_code):
    """List all polls for a meeting code."""
    polls = Poll.query.filter_by(meeting_code=meeting_code).order_by(Poll.created_at.desc()).all()
    return jsonify([p.to_dict() for p in polls]), 200


@polls_bp.route("/<string:poll_id>/vote", methods=["POST"])
@jwt_required()
def vote_poll(poll_id):
    """Submit a vote for a poll option."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    option_ids = data.get("option_ids", [])

    if not option_ids:
        return jsonify({"error": "option_ids is required"}), 400

    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"error": "Poll not found"}), 404

    if poll.is_closed:
        return jsonify({"error": "Poll is closed"}), 400

    # Clear existing votes if single-choice
    if not poll.is_multiselect:
        PollVote.query.filter_by(poll_id=poll.id, user_id=current_user_id).delete()

    for opt_id in option_ids:
        opt = PollOption.query.filter_by(id=opt_id, poll_id=poll_id).first()
        if opt:
            existing = PollVote.query.filter_by(poll_id=poll_id, option_id=opt_id, user_id=current_user_id).first()
            if not existing:
                vote = PollVote(poll_id=poll_id, option_id=opt_id, user_id=current_user_id)
                db.session.add(vote)

    db.session.commit()
    return jsonify(poll.to_dict()), 200


@polls_bp.route("/<string:poll_id>/publish", methods=["POST"])
@jwt_required()
def publish_poll(poll_id):
    """Publish poll results to meeting room."""
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"error": "Poll not found"}), 404

    poll.is_published = True
    db.session.commit()
    return jsonify(poll.to_dict()), 200


@polls_bp.route("/<string:poll_id>/close", methods=["POST"])
@jwt_required()
def close_poll(poll_id):
    """Close poll for voting."""
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"error": "Poll not found"}), 404

    poll.is_closed = True
    db.session.commit()
    return jsonify(poll.to_dict()), 200
