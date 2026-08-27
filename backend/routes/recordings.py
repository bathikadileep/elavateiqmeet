"""
ElevateIQ — Meeting Recordings & HLS Streaming REST APIs
==========================================================
API Endpoints:
  - POST /api/recordings/start                 → Start cloud recording session
  - POST /api/recordings/stop                  → Stop recording & trigger HLS transcoding
  - GET  /api/recordings/meeting/<code >        → List recordings for meeting
  - GET  /api/recordings/<id >                  → Get recording details
  - GET  /api/recordings/<id >/stream           → Stream HLS playlist / segments
"""

import os
import uuid
import logging
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import MeetingRecording, Meeting
from backend.workers.recorder_worker import start_recording_worker, stop_recording_worker
from backend.services.hls_transcoder import HLSTranscoderService

recordings_bp = Blueprint("recordings", __name__, url_prefix="/api/recordings")
log = logging.getLogger("elevateiq.recordings")


@recordings_bp.route("/start", methods=["POST"])
@jwt_required()
def start_recording():
    """Start cloud recording session."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    meeting_code = data.get("meeting_code")

    if not meeting_code:
        return jsonify({"error": "meeting_code is required"}), 400

    meeting = Meeting.query.filter_by(meeting_code=meeting_code).first()
    meeting_id = meeting.id if meeting else uuid.uuid4().hex

    rec = MeetingRecording(
        meeting_id=meeting_id,
        initiated_by=current_user_id,
        status="processing"
    )
    db.session.add(rec)
    db.session.commit()

    start_recording_worker(meeting_code, rec.id)
    log.info("Started recording id=%s for meeting_code=%s", rec.id, meeting_code)
    return jsonify(rec.to_dict()), 201


@recordings_bp.route("/stop", methods=["POST"])
@jwt_required()
def stop_recording():
    """Stop recording session and trigger HLS transcoding."""
    data = request.get_json() or {}
    meeting_code = data.get("meeting_code")

    if not meeting_code:
        return jsonify({"error": "meeting_code is required"}), 400

    meta = stop_recording_worker(meeting_code)
    if not meta:
        return jsonify({"error": "No active recording found for this meeting"}), 404

    rec = MeetingRecording.query.get(meta["recording_id"])
    if rec:
        rec.status = "available"
        rec.duration_seconds = meta.get("duration_seconds", 30)
        rec.size_bytes = meta.get("size_bytes", 1024)
        rec.download_url = meta.get("download_url", "")
        db.session.commit()

    # Trigger HLS transcoding
    hls_dir = os.path.join("uploads", "recordings", f"hls_{meta['recording_id']}")
    hls_meta = HLSTranscoderService.transcode_to_hls(meta.get("storage_path", ""), hls_dir)

    response_data = rec.to_dict() if rec else meta
    response_data["hls_playlist_url"] = f"/api/recordings/{meta['recording_id']}/stream/index.m3u8"
    return jsonify(response_data), 200


@recordings_bp.route("/meeting/<string:meeting_code>", methods=["GET"])
@jwt_required()
def list_recordings(meeting_code):
    """List recordings for a meeting."""
    meeting = Meeting.query.filter_by(meeting_code=meeting_code).first()
    if not meeting:
        return jsonify([]), 200
    recs = MeetingRecording.query.filter_by(meeting_id=meeting.id).all()
    return jsonify([r.to_dict() for r in recs]), 200


@recordings_bp.route("/<string:rec_id>", methods=["GET"])
@jwt_required()
def get_recording(rec_id):
    """Get single recording details."""
    rec = MeetingRecording.query.get(rec_id)
    if not rec:
        return jsonify({"error": "Recording not found"}), 404
    return jsonify(rec.to_dict()), 200


@recordings_bp.route("/<string:rec_id>/stream/<path:filename>", methods=["GET"])
def stream_hls(rec_id, filename):
    """Serve HLS playlist (.m3u8) or TS media segments."""
    hls_dir = os.path.abspath(os.path.join("uploads", "recordings", f"hls_{rec_id}"))
    file_path = os.path.join(hls_dir, filename)

    if not os.path.exists(file_path):
        # Auto-generate HLS playlist on-the-fly if missing
        HLSTranscoderService.transcode_to_hls("", hls_dir)

    if os.path.exists(file_path):
        mime = "application/x-mpegURL" if filename.endswith(".m3u8") else "video/MP2T"
        return send_file(file_path, mimetype=mime)

    return jsonify({"error": "HLS stream file not found"}), 404
