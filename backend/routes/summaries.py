"""
ElevateIQ — AI Meeting Summaries & Transcripts REST APIs
=========================================================
API Endpoints:
  - POST /api/summaries/transcript            → Store transcript line
  - GET  /api/summaries/transcript/<code >     → Retrieve full transcript
  - POST /api/summaries/generate               → Generate AI summary via LLM/NLP
  - GET  /api/summaries/meeting/<code >        → Fetch stored summary
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import MeetingTranscriptLine, MeetingSummary, ActionItem
from backend.services.ai_summarizer import AISummarizerService

summaries_bp = Blueprint("summaries", __name__, url_prefix="/api/summaries")
log = logging.getLogger("elevateiq.summaries")


@summaries_bp.route("/transcript", methods=["POST"])
@jwt_required()
def add_transcript_line():
    """Record a line of speech transcript."""
    data = request.get_json() or {}
    meeting_code = data.get("meeting_code")
    speaker_name = data.get("speaker_name", "Speaker")
    transcript_text = data.get("transcript_text")

    if not meeting_code or not transcript_text:
        return jsonify({"error": "meeting_code and transcript_text are required"}), 400

    line = MeetingTranscriptLine(
        meeting_code=meeting_code,
        speaker_name=speaker_name,
        transcript_text=transcript_text.strip()
    )
    db.session.add(line)
    db.session.commit()
    return jsonify(line.to_dict()), 201


@summaries_bp.route("/transcript/<string:meeting_code>", methods=["GET"])
@jwt_required()
def get_transcript(meeting_code):
    """Get full meeting transcript."""
    lines = MeetingTranscriptLine.query.filter_by(meeting_code=meeting_code).order_by(MeetingTranscriptLine.timestamp.asc()).all()
    return jsonify([l.to_dict() for l in lines]), 200


@summaries_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_summary():
    """Trigger AI summarization for a meeting transcript."""
    data = request.get_json() or {}
    meeting_code = data.get("meeting_code")

    if not meeting_code:
        return jsonify({"error": "meeting_code is required"}), 400

    lines = MeetingTranscriptLine.query.filter_by(meeting_code=meeting_code).order_by(MeetingTranscriptLine.timestamp.asc()).all()
    raw_lines = [l.to_dict() for l in lines]

    summary_data = AISummarizerService.generate_meeting_summary(raw_lines)

    # Delete existing summary if regenerating
    existing = MeetingSummary.query.filter_by(meeting_code=meeting_code).first()
    if existing:
        db.session.delete(existing)
        db.session.flush()

    summary = MeetingSummary(
        meeting_code=meeting_code,
        executive_summary=summary_data.get("executive_summary", ""),
        key_decisions=summary_data.get("key_decisions", []),
        sentiment_score=summary_data.get("sentiment_score", "positive"),
        sentiment_value=summary_data.get("sentiment_value", "0.85")
    )
    db.session.add(summary)
    db.session.flush()

    for item in summary_data.get("action_items", []):
        action = ActionItem(
            summary_id=summary.id,
            task_description=item.get("task_description", "Task"),
            assigned_to=item.get("assigned_to", "Unassigned"),
            due_date=item.get("due_date", "Next Sprint")
        )
        db.session.add(action)

    db.session.commit()
    log.info("Generated AI summary for meeting %s", meeting_code)
    return jsonify(summary.to_dict()), 201


@summaries_bp.route("/meeting/<string:meeting_code>", methods=["GET"])
@jwt_required()
def get_summary(meeting_code):
    """Retrieve stored AI summary for a meeting."""
    summary = MeetingSummary.query.filter_by(meeting_code=meeting_code).first()
    if not summary:
        return jsonify({"error": "Summary not generated yet for this meeting"}), 404
    return jsonify(summary.to_dict()), 200
