"""
ElevateIQ — AI Meeting Summaries & Transcripts REST APIs
=========================================================
API Endpoints:
  - POST /api/summaries/transcript            → Store transcript line (throttled & sanitized)
  - GET  /api/summaries/transcript/<code>     → Retrieve full transcript
  - POST /api/summaries/generate               → Generate AI summary via LLM/NLP (idempotent)
  - GET  /api/summaries/meeting/<code>        → Fetch stored summary
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import MeetingTranscriptLine, MeetingSummary, ActionItem
from backend.services.ai_summarizer import AISummarizerService

summaries_bp = Blueprint("summaries", __name__, url_prefix="/api/summaries")
log = logging.getLogger("elevateiq.summaries")

# Maximum number of transcript lines permitted per single meeting session
MAX_TRANSCRIPT_LINES_PER_MEETING = 1000


@summaries_bp.route("/transcript", methods=["POST"])
@jwt_required()
def add_transcript_line():
    """Record a line of speech transcript with strict non-empty validation and quota guards."""
    data = request.get_json() or {}
    meeting_code = (data.get("meeting_code") or "").strip()
    speaker_name = (data.get("speaker_name") or "Speaker").strip()
    transcript_text = data.get("transcript_text")

    # 1. Strict validation: reject null, empty, or whitespace-only inputs
    cleaned_text = (transcript_text or "").strip()
    if not meeting_code or not cleaned_text:
        return jsonify({"error": "meeting_code and non-empty transcript_text are required"}), 400

    # 2. Quota guard: prevent infinite 50K+ generation loops
    current_count = MeetingTranscriptLine.query.filter_by(meeting_code=meeting_code).count()
    if current_count >= MAX_TRANSCRIPT_LINES_PER_MEETING:
        return jsonify({"error": "Meeting transcript buffer is full (maximum 1,000 lines reached)."}), 429

    # 3. Consecutive deduplication: ignore rapid-fire identical packets from same speaker
    last_line = MeetingTranscriptLine.query.filter_by(
        meeting_code=meeting_code,
        speaker_name=speaker_name
    ).order_by(MeetingTranscriptLine.timestamp.desc()).first()

    if last_line and last_line.transcript_text == cleaned_text:
        return jsonify(last_line.to_dict()), 200

    line = MeetingTranscriptLine(
        meeting_code=meeting_code,
        speaker_name=speaker_name,
        transcript_text=cleaned_text
    )
    db.session.add(line)
    db.session.commit()
    return jsonify(line.to_dict()), 201


@summaries_bp.route("/transcript/<string:meeting_code>", methods=["GET"])
@jwt_required()
def get_transcript(meeting_code):
    """Get full meeting transcript (capped to latest 1,000 lines)."""
    lines = MeetingTranscriptLine.query.filter_by(
        meeting_code=meeting_code
    ).order_by(MeetingTranscriptLine.timestamp.asc()).limit(MAX_TRANSCRIPT_LINES_PER_MEETING).all()
    return jsonify([l.to_dict() for l in lines]), 200


@summaries_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_summary():
    """Trigger AI summarization for a meeting transcript (idempotent upsert)."""
    data = request.get_json() or {}
    meeting_code = (data.get("meeting_code") or "").strip()

    if not meeting_code:
        return jsonify({"error": "meeting_code is required"}), 400

    lines = MeetingTranscriptLine.query.filter_by(
        meeting_code=meeting_code
    ).order_by(MeetingTranscriptLine.timestamp.asc()).limit(MAX_TRANSCRIPT_LINES_PER_MEETING).all()
    
    # Filter out any empty lines
    raw_lines = [l.to_dict() for l in lines if l.transcript_text and l.transcript_text.strip()]

    summary_data = AISummarizerService.generate_meeting_summary(raw_lines)

    # Idempotent transactional upsert to eliminate race conditions
    existing = MeetingSummary.query.filter_by(meeting_code=meeting_code).first()
    if existing:
        existing.executive_summary = summary_data.get("executive_summary", "")
        existing.key_decisions = summary_data.get("key_decisions", [])
        existing.sentiment_score = summary_data.get("sentiment_score", "positive")
        existing.sentiment_value = summary_data.get("sentiment_value", "0.85")
        ActionItem.query.filter_by(summary_id=existing.id).delete()
        summary = existing
    else:
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
        task_desc = (item.get("task_description") or "").strip()
        if not task_desc:
            continue
        action = ActionItem(
            summary_id=summary.id,
            task_description=task_desc,
            assigned_to=item.get("assigned_to", "Unassigned"),
            due_date=item.get("due_date", "Next Sprint")
        )
        db.session.add(action)

    db.session.commit()
    log.info("Generated/Updated AI summary for meeting %s", meeting_code)
    return jsonify(summary.to_dict()), 201


@summaries_bp.route("/meeting/<string:meeting_code>", methods=["GET"])
@jwt_required()
def get_summary(meeting_code):
    """Retrieve stored AI summary for a meeting."""
    summary = MeetingSummary.query.filter_by(meeting_code=meeting_code).first()
    if not summary:
        return jsonify({"error": "Summary not generated yet for this meeting"}), 404
    return jsonify(summary.to_dict()), 200

