"""
ElevateIQ — Security Audit Log Pipeline & Event Tracking Test Suite
====================================================================
Verifies security audit log creation, event classification (SSO_LOGIN, SESSION_REVOKED, DLP_OFFENSE),
actor tracking, and JSON details field serialization in SQLite/Postgres.
"""

import unittest
from datetime import datetime, timezone
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, SecurityAuditLog


class SecurityAuditPipelineTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.actor = User(
            username="sec_actor",
            email="sec_actor@elevateiq.com",
            password_hash="hash",
            display_name="Security Actor",
            status="active",
        )
        db.session.add(self.actor)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_audit_log_creation_and_query(self):
        """Test logging security audit event and filtering by event type."""
        log_entry = SecurityAuditLog(
            event_type="SSO_LOGIN",
            actor_id=self.actor.id,
            details={"provider": "okta", "ip": "192.168.1.100", "auth_method": "SAML2"}
        )
        db.session.add(log_entry)
        db.session.commit()

        fetched = SecurityAuditLog.query.filter_by(event_type="SSO_LOGIN").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.actor_id, self.actor.id)
        self.assertEqual(fetched.details["provider"], "okta")

    def test_dlp_offense_audit_log(self):
        """Test recording DLP offense security audit entry."""
        log_entry = SecurityAuditLog(
            event_type="DLP_OFFENSE",
            actor_id=self.actor.id,
            details={"offense": "SSN_DETECTED", "action": "BLOCKED"}
        )
        db.session.add(log_entry)
        db.session.commit()

        fetched = SecurityAuditLog.query.filter_by(event_type="DLP_OFFENSE").first()
        self.assertEqual(fetched.details["action"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
