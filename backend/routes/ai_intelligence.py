"""
ElevateIQ — AI Intelligence & Diarization REST API Blueprint
=============================================================
API Endpoints:
  - GET  /api/ai-intelligence/diarization/<code> → Get speaker talk-time & diarization analytics
  - POST /api/ai-intelligence/translate        → Translate closed caption text to target language
  - GET  /api/ai-intelligence/languages        → List supported caption translation languages
  - POST /api/ai-intelligence/dispatch/slack   → Post meeting summary block to Slack webhook
"""

import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from backend.models.models import MeetingTranscriptLine
from backend.services.ai.diarization_service import DiarizationService
from backend.services.ai.translation_service import TranslationService
from backend.services.integrations_service import IntegrationsService

ai_intel_bp = Blueprint("ai_intelligence", __name__, url_prefix="/api/ai-intelligence")
log = logging.getLogger("elevateiq.ai_intelligence")


@ai_intel_bp.route("/diarization/<string:meeting_code>", methods=["GET"])
@jwt_required()
def get_diarization_stats(meeting_code):
    """Retrieve speaker talk-time percentages and turn analytics for a meeting."""
    lines = MeetingTranscriptLine.query.filter_by(meeting_code=meeting_code).all()
    raw_lines = [l.to_dict() for l in lines]
    stats = DiarizationService.calculate_speaker_talktime(raw_lines)
    interjections = DiarizationService.detect_interjections_and_overlaps(raw_lines)
    stats["interjections"] = interjections
    return jsonify(stats), 200


@ai_intel_bp.route("/translate", methods=["POST"])

def translate_caption():
    """Translate live closed caption snippet into target language."""
    data = request.get_json() or {}
    text = data.get("text", "")
    target_lang = data.get("target_lang", "es")
    source_lang = data.get("source_lang", "en")

    result = TranslationService.translate_text(text, target_lang, source_lang)
    return jsonify(result), 200


@ai_intel_bp.route("/languages", methods=["GET"])
def get_languages():
    """Fetch list of supported multi-language closed caption translation targets."""
    return jsonify(TranslationService.get_supported_languages()), 200


@ai_intel_bp.route("/dispatch/slack", methods=["POST"])
@jwt_required()
def dispatch_slack():
    """Post AI summary and action items to Slack webhook."""
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url")
    room_code = data.get("room_code", "N/A")
    summary_text = data.get("summary_text", "")
    action_items = data.get("action_items", [])

    if not webhook_url:
        return jsonify({"error": "webhook_url parameter is required"}), 400

    res = IntegrationsService.dispatch_summary_to_slack(webhook_url, room_code, summary_text, action_items)
    return jsonify(res), 200
