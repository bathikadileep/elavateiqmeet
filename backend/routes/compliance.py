"""
ElevateIQ — Compliance & Governance REST API Endpoints
======================================================
API Endpoints:
  - GET  /api/compliance/export              → Export user GDPR data ZIP bundle
  - POST /api/compliance/forget              → Execute Right to be Forgotten (GDPR Art. 17)
  - GET  /api/compliance/soc2-report         → Fetch SOC2 compliance report
  - GET  /api/compliance/audit-integrity     → Verify audit log cryptographic integrity
  - GET  /api/compliance/retention-audit     → Scan data retention thresholds
"""

import logging
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.compliance_service import ComplianceService
from backend.services.audit_logger import AuditLoggerService

compliance_bp = Blueprint("compliance", __name__, url_prefix="/api/compliance")
log = logging.getLogger("elevateiq.compliance")


@compliance_bp.route("/export", methods=["GET"])
@jwt_required()
def export_user_data():
    """Download GDPR Article 20 personal data archive as a ZIP file."""
    current_user_id = get_jwt_identity()
    try:
        zip_bytes = ComplianceService.export_user_data_bundle(current_user_id)
        return Response(
            zip_bytes,
            mimetype="application/zip",
            headers={"Content-Disposition": f"attachment; filename=gdpr_data_export_{current_user_id[:8]}.zip"}
        )
    except Exception as e:
        log.warning("Data export failed for user %s: %s", current_user_id, e)
        return jsonify({"error": str(e)}), 400


@compliance_bp.route("/forget", methods=["POST"])
@jwt_required()
def right_to_be_forgotten():
    """Execute GDPR Article 17 Right to be Forgotten for the current authenticated user."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    confirmation = data.get("confirmation", "").strip().lower()

    if confirmation != "delete my account permanently":
        return jsonify({
            "error": "Confirmation phrase mismatch. Must submit 'delete my account permanently'."
        }), 400

    result = ComplianceService.execute_right_to_be_forgotten(current_user_id)
    return jsonify(result), 200


@compliance_bp.route("/soc2-report", methods=["GET"])
@jwt_required()
def get_soc2_report():
    """Retrieve SOC2 Type II compliance audit status report (Admin only)."""
    report = AuditLoggerService.generate_soc2_compliance_report()
    return jsonify(report), 200


@compliance_bp.route("/audit-integrity", methods=["GET"])
@jwt_required()
def verify_audit_integrity():
    """Verify cryptographic hash chain integrity of security audit logs."""
    integrity = AuditLoggerService.verify_audit_trail_integrity()
    return jsonify(integrity), 200


@compliance_bp.route("/retention-audit", methods=["GET"])
@jwt_required()
def audit_retention():
    """Audit PII data retention threshold limits."""
    days = request.args.get("days", default=90, type=int)
    res = ComplianceService.audit_pii_data_retention(days)
    return jsonify(res), 200
