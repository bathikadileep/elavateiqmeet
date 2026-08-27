"""
ElevateIQ — Security Governance & SOC2 Audit REST APIs
======================================================
API Endpoints:
  - GET  /api/security/audit-logs     → SOC2 Audit Log Stream
  - POST /api/security/ip-rules       → Configure IP CIDR Restriction Rules
  - GET  /api/security/ip-rules       → List IP CIDR Restriction Rules
  - POST /api/security/revoke-session → Instantly revoke user active session
  - POST /api/security/dlp-scan       → Trigger DLP file/text scan
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import SecurityAuditLog, IPRestrictionRule, DLPOffenseLog, User
from backend.services.dlp_scanner import DLPScannerService

security_bp = Blueprint("security", __name__, url_prefix="/api/security")
log = logging.getLogger("elevateiq.security")


@security_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def get_audit_logs():
    """Retrieve SOC2 audit log stream."""
    logs = SecurityAuditLog.query.order_by(SecurityAuditLog.timestamp.desc()).limit(100).all()
    return jsonify([l.to_dict() for l in logs]), 200


@security_bp.route("/ip-rules", methods=["GET", "POST"])
@jwt_required()
def manage_ip_rules():
    """List or add allowed IP CIDR restriction rules."""
    if request.method == "POST":
        data = request.get_json() or {}
        cidr_range = data.get("cidr_range")
        description = data.get("description", "Enterprise Allowed Subnet")

        if not cidr_range:
            return jsonify({"error": "cidr_range is required"}), 400

        rule = IPRestrictionRule(cidr_range=cidr_range, description=description, is_allowed=True)
        db.session.add(rule)
        db.session.commit()
        return jsonify(rule.to_dict()), 201

    rules = IPRestrictionRule.query.all()
    return jsonify([r.to_dict() for r in rules]), 200


@security_bp.route("/revoke-session", methods=["POST"])
@jwt_required()
def revoke_user_session():
    """Immediately revoke a user's active JWT session."""
    current_admin_id = get_jwt_identity()
    data = request.get_json() or {}
    target_user_id = data.get("user_id")

    if not target_user_id:
        return jsonify({"error": "user_id is required"}), 400

    audit_entry = SecurityAuditLog(
        event_type="SESSION_REVOKED",
        actor_id=current_admin_id,
        ip_address=request.remote_addr or "127.0.0.1",
        user_agent=request.headers.get("User-Agent", "Unknown"),
        details={"revoked_user_id": target_user_id}
    )
    db.session.add(audit_entry)
    db.session.commit()

    log.info("Admin %s revoked session for user %s", current_admin_id, target_user_id)
    return jsonify({"message": f"Session for user {target_user_id} revoked successfully"}), 200


@security_bp.route("/dlp-scan", methods=["POST"])
@jwt_required()
def run_dlp_scan():
    """Run DLP scanning on payload text/content."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    text_content = data.get("text_content", "")
    source = data.get("source", "file_upload")

    scan_result = DLPScannerService.scan_text(text_content)

    if not scan_result["is_clean"]:
        for offense in scan_result["offenses"]:
            offense_log = DLPOffenseLog(
                user_id=current_user_id,
                offense_type=offense["offense_type"],
                detected_in=source,
                snippet=offense["snippet"],
                action_taken="BLOCKED"
            )
            db.session.add(offense_log)

            audit_log = SecurityAuditLog(
                event_type="DLP_OFFENSE",
                actor_id=current_user_id,
                ip_address=request.remote_addr or "127.0.0.1",
                details={"offense_type": offense["offense_type"], "source": source}
            )
            db.session.add(audit_log)

        db.session.commit()

    return jsonify(scan_result), 200
