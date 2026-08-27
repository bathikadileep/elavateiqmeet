"""
ElevateIQ — Enterprise Reporting System Blueprint
==================================================
Endpoints:
  GET /api/v1/reports/attendance    → Attendance Compliance Report (JSON/CSV/Excel)
  GET /api/v1/reports/meetings      → Meeting History Report (JSON/CSV/Excel)
  GET /api/v1/reports/user-activity → User Activity & Engagement Report (JSON/CSV/Excel)
"""

import io
import csv
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import (
    Meeting,
    MeetingParticipant,
    AttendanceLog,
    User,
)
from backend.core.errors import BadRequestError

log = logging.getLogger("elevateiq.reports")

reports_bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")


def generate_csv_response(filename: str, headers: list, rows: list) -> Response:
    """Helper formatting rows into downloadable CSV HTTP Response."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
    return response


# ── 1. Attendance Report Endpoint ─────────────────────────────────────────────

@reports_bp.route("/attendance", methods=["GET"])
@jwt_required()
def get_attendance_report():
    """
    GET /api/v1/reports/attendance?format=json|csv|excel&meeting_id=...
    """
    fmt = request.args.get("format", "json").lower()
    meeting_id = request.args.get("meeting_id")

    stmt = db.select(AttendanceLog).order_by(AttendanceLog.event_at.desc())
    if meeting_id:
        stmt = stmt.where(AttendanceLog.meeting_id == meeting_id)

    logs = db.session.scalars(stmt.limit(100)).all()

    data_rows = []
    for l in logs:
        m = db.session.get(Meeting, l.meeting_id)
        u = db.session.get(User, l.user_id) if l.user_id else None
        user_name = u.display_name if u else "Guest"
        meeting_title = m.title if m else "N/A"
        dur_mins = round(l.duration_seconds / 60, 1) if l.duration_seconds else 0

        data_rows.append([
            l.id,
            meeting_title,
            user_name,
            l.event,
            l.event_at.isoformat() + "Z",
            dur_mins,
            "100%" if l.event == "left" else "Active",
        ])

    headers = ["Log ID", "Meeting Title", "Participant", "Event", "Event Timestamp", "Duration (Mins)", "Compliance Status"]

    if fmt in ["csv", "excel"]:
        filename = f"Attendance_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        return generate_csv_response(filename, headers, data_rows)

    # JSON Return
    result = [
        {
            "id": r[0],
            "meeting_title": r[1],
            "participant": r[2],
            "event": r[3],
            "event_at": r[4],
            "duration_minutes": r[5],
            "status": r[6],
        }
        for r in data_rows
    ]
    return jsonify({"report": "attendance", "total_records": len(result), "data": result}), 200


# ── 2. Meeting Report Endpoint ────────────────────────────────────────────────

@reports_bp.route("/meetings", methods=["GET"])
@jwt_required()
def get_meeting_report():
    """
    GET /api/v1/reports/meetings?format=json|csv|excel
    """
    fmt = request.args.get("format", "json").lower()

    meetings = db.session.scalars(
        db.select(Meeting).where(Meeting.is_deleted == False).order_by(Meeting.created_at.desc()).limit(100)
    ).all()

    data_rows = []
    for m in meetings:
        host = db.session.get(User, m.host_id) if m.host_id else None
        participant_count = len(m.participants)

        data_rows.append([
            m.id,
            m.meeting_code,
            m.title,
            host.display_name if host else "Unknown",
            m.meeting_type,
            m.status,
            participant_count,
            m.created_at.isoformat() + "Z",
        ])

    headers = ["Meeting ID", "Meeting Code", "Title", "Host", "Type", "Status", "Participant Count", "Created At"]

    if fmt in ["csv", "excel"]:
        filename = f"Meeting_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        return generate_csv_response(filename, headers, data_rows)

    result = [
        {
            "id": r[0],
            "meeting_code": r[1],
            "title": r[2],
            "host_name": r[3],
            "meeting_type": r[4],
            "status": r[5],
            "participant_count": r[6],
            "created_at": r[7],
        }
        for r in data_rows
    ]
    return jsonify({"report": "meetings", "total_records": len(result), "data": result}), 200


# ── 3. User Activity Report Endpoint ──────────────────────────────────────────

@reports_bp.route("/user-activity", methods=["GET"])
@jwt_required()
def get_user_activity_report():
    """
    GET /api/v1/reports/user-activity?format=json|csv|excel
    """
    fmt = request.args.get("format", "json").lower()

    users = db.session.scalars(
        db.select(User).where(User.is_deleted == False).order_by(User.created_at.desc()).limit(100)
    ).all()

    data_rows = []
    for u in users:
        hosted_count = len(u.hosted_meetings)
        joined_count = len(u.participations)
        total_seconds = db.session.scalar(
            db.select(db.func.sum(AttendanceLog.duration_seconds)).where(AttendanceLog.user_id == u.id)
        ) or 0
        active_hours = round(total_seconds / 3600, 1)

        data_rows.append([
            u.id,
            u.username,
            u.email,
            u.display_name or u.username,
            u.status,
            hosted_count,
            joined_count,
            active_hours,
            u.created_at.isoformat() + "Z",
        ])

    headers = ["User ID", "Username", "Email", "Display Name", "Status", "Hosted Meetings", "Joined Meetings", "Active Hours", "Joined Platform Date"]

    if fmt in ["csv", "excel"]:
        filename = f"User_Activity_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        return generate_csv_response(filename, headers, data_rows)

    result = [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "display_name": r[3],
            "status": r[4],
            "hosted_count": r[5],
            "joined_count": r[6],
            "active_hours": r[7],
            "created_at": r[8],
        }
        for r in data_rows
    ]
    return jsonify({"report": "user_activity", "total_records": len(result), "data": result}), 200
