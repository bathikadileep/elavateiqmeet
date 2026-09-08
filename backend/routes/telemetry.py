"""
ElevateIQ — WebRTC Network Telemetry REST API Blueprint
========================================================
API Endpoints:
  - POST /api/telemetry/report   → Submit WebRTC getStats() telemetry package
  - GET  /api/telemetry/qoe/<code> → Fetch room aggregate QoE performance health
"""

import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.telemetry_service import TelemetryService

telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/telemetry")
log = logging.getLogger("elevateiq.telemetry")


@telemetry_bp.route("/report", methods=["POST"])
@jwt_required()
def submit_telemetry():
    """Submit WebRTC QoE stats report from browser client."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    room_code = data.get("room_code", "").strip()
    stats = data.get("stats", {})

    if not room_code:
        return jsonify({"error": "room_code parameter is required"}), 400

    qoe_report = TelemetryService.process_client_telemetry_report(room_code, current_user_id, stats)
    return jsonify(qoe_report), 200
