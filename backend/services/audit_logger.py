"""
ElevateIQ — Immutable Audit Logging & SOC2 Compliance Engine
=============================================================
Provides SHA-256 cryptographic hash-chained audit logging, tamper detection,
and SOC2 Type II compliance reporting for enterprise security governance.
"""

import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.extensions import db
from backend.models.models import SecurityAuditLog, User, Meeting

log = logging.getLogger("elevateiq.services.audit_logger")


class AuditLoggerService:
    """Cryptographic Audit Log Engine & SOC2 Compliance Inspector."""

    @staticmethod
    def calculate_log_entry_hash(previous_hash: str, user_id: Optional[str], event_type: str, timestamp: str, details_str: str) -> str:
        """
        Compute SHA-256 hash incorporating the previous entry's hash to form
        an immutable, tamper-evident cryptographic blockchain of audit logs.
        """
        payload = f"{previous_hash}|{user_id or ''}|{event_type}|{timestamp}|{details_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def record_audit_event(event_type: str, user_id: Optional[str] = None, ip_address: str = "127.0.0.1", details: Optional[Dict[str, Any]] = None) -> SecurityAuditLog:
        """Record a security audit event with cryptographic hash chaining."""
        details_dict = details or {}
        details_str = json.dumps(details_dict, sort_keys=True)
        timestamp_str = datetime.now(timezone.utc).isoformat()

        # Fetch last recorded audit entry to get previous hash
        last_entry = SecurityAuditLog.query.order_by(SecurityAuditLog.timestamp.desc()).first()
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        if last_entry and last_entry.details:
            prev_hash = last_entry.details.get("_crypto_entry_hash", prev_hash)

        entry_hash = AuditLoggerService.calculate_log_entry_hash(
            prev_hash, user_id, event_type, timestamp_str, details_str
        )

        details_dict["_crypto_prev_hash"] = prev_hash
        details_dict["_crypto_entry_hash"] = entry_hash
        details_dict["_crypto_timestamp_str"] = timestamp_str

        log_entry = SecurityAuditLog(
            actor_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            details=details_dict,
        )

        db.session.add(log_entry)
        db.session.commit()
        log.info("Recorded audit event '%s' for user %s | Hash: %s", event_type, user_id, entry_hash[:12])
        return log_entry

    @staticmethod
    def verify_audit_trail_integrity() -> Dict[str, Any]:
        """
        Scan all audit log records and verify cryptographic hash chain integrity
        to detect database tampering or missing audit logs (SOC2 CC6.1 audit requirement).
        """
        entries = SecurityAuditLog.query.order_by(SecurityAuditLog.timestamp.asc()).all()
        total_records = len(entries)
        tampered_count = 0
        corrupted_ids = []

        expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"

        for entry in entries:
            details_map = entry.details or {}
            stored_hash = details_map.get("_crypto_entry_hash")

            if stored_hash:
                # Re-calculate hash
                details_copy = {k: v for k, v in details_map.items() if not k.startswith("_crypto_")}
                details_str = json.dumps(details_copy, sort_keys=True)
                timestamp_str = details_map.get("_crypto_timestamp_str") or (entry.timestamp.isoformat() if entry.timestamp else "")

                computed_hash = AuditLoggerService.calculate_log_entry_hash(
                    expected_prev_hash, entry.actor_id, entry.event_type, timestamp_str, details_str
                )

                if computed_hash != stored_hash:
                    tampered_count += 1
                    corrupted_ids.append(entry.id)
                expected_prev_hash = stored_hash
            else:
                expected_prev_hash = getattr(entry, "id", expected_prev_hash)

        return {
            "total_audit_records": total_records,
            "chain_integrity_status": "VALID" if tampered_count == 0 else "CORRUPTED",
            "tampered_records_count": tampered_count,
            "corrupted_log_ids": corrupted_ids,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def generate_soc2_compliance_report() -> Dict[str, Any]:
        """Generate SOC2 Type II Security & Audit Compliance Executive Brief."""
        integrity_check = AuditLoggerService.verify_audit_trail_integrity()

        total_users = User.query.count()
        active_users = User.query.filter_by(status="active").count()
        total_meetings = Meeting.query.count()

        return {
            "report_title": "ElevateIQ Meet SOC2 Type II Security Compliance Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "compliance_standards": ["SOC2 Type II", "GDPR Article 32", "ISO/IEC 27001"],
            "security_controls": {
                "audit_log_encryption": "SHA-256 Hash Chained",
                "log_integrity_status": integrity_check["chain_integrity_status"],
                "total_audit_logs": integrity_check["total_audit_records"],
                "authentication_enforcement": "JWT + Bcrypt Blowfish Cost 12",
                "transport_layer_security": "TLS 1.3 / HTTPS / WSS",
            },
            "environment_metrics": {
                "total_registered_users": total_users,
                "active_user_accounts": active_users,
                "total_meeting_sessions_hosted": total_meetings,
            }
        }
