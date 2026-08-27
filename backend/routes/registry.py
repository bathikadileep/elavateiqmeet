"""
ElevateIQ — Blueprint Registry
================================
Central hub for registering all Flask Blueprints onto the application.
Add every new blueprint import + registration here, and nowhere else.

Convention:
  - All REST blueprints mount under /api/v1/<resource>
  - Socket.IO namespaces are registered separately in sockets/
"""

import logging
from flask import Flask

log = logging.getLogger("elevateiq.registry")


def register_blueprints(app: Flask) -> None:
    """
    Import and register all application blueprints.
    Called once inside create_app().

    Registration order matters when blueprints share URL prefixes —
    more specific routes should be registered before catch-all routes.
    """

    # ── Health & System ───────────────────────────────────────────────────────
    from backend.routes.health import health_bp
    app.register_blueprint(health_bp)
    log.debug("Blueprint registered: health")

    # ── Authentication ────────────────────────────────────────────────────────
    from backend.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    log.debug("Blueprint registered: auth")

    # ── Dashboard ─────────────────────────────────────────────────────────────
    from backend.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    log.debug("Blueprint registered: dashboard")

    # ── Meetings ──────────────────────────────────────────────────────────────
    from backend.routes.meetings import meetings_bp
    app.register_blueprint(meetings_bp)
    log.debug("Blueprint registered: meetings")

    # ── Attendance ────────────────────────────────────────────────────────────
    from backend.routes.attendance import attendance_bp
    app.register_blueprint(attendance_bp)
    log.debug("Blueprint registered: attendance")

    # ── Files ─────────────────────────────────────────────────────────────────
    from backend.routes.files import files_bp
    app.register_blueprint(files_bp)
    log.debug("Blueprint registered: files")

    # ── Notifications ─────────────────────────────────────────────────────────
    from backend.routes.notifications import notifications_bp
    app.register_blueprint(notifications_bp)
    log.debug("Blueprint registered: notifications")

    # ── Admin Panel ───────────────────────────────────────────────────────────
    from backend.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    log.debug("Blueprint registered: admin")

    # ── Reporting System ──────────────────────────────────────────────────────
    from backend.routes.reports import reports_bp
    app.register_blueprint(reports_bp)
    log.debug("Blueprint registered: reports")

    # ── In-Meeting Polling ───────────────────────────────────────────────────
    from backend.routes.polls import polls_bp
    app.register_blueprint(polls_bp)
    log.debug("Blueprint registered: polls")

    # ── Breakout Rooms ────────────────────────────────────────────────────────
    from backend.routes.breakout import breakout_bp
    app.register_blueprint(breakout_bp)
    log.debug("Blueprint registered: breakout")

    # ── AI Meeting Summaries & Transcripts ────────────────────────────────────
    from backend.routes.summaries import summaries_bp
    app.register_blueprint(summaries_bp)
    log.debug("Blueprint registered: summaries")

    # ── Cloud Recordings & HLS Streams ────────────────────────────────────────
    from backend.routes.recordings import recordings_bp
    app.register_blueprint(recordings_bp)
    log.debug("Blueprint registered: recordings")

    # ── Enterprise OAuth2 & SSO ───────────────────────────────────────────────
    from backend.routes.sso import sso_bp
    app.register_blueprint(sso_bp)
    log.debug("Blueprint registered: sso")

    # ── Security Governance & SOC2 Audit ──────────────────────────────────────
    from backend.routes.security_audit import security_bp
    app.register_blueprint(security_bp)
    log.debug("Blueprint registered: security")

    # ── Developer API Gateway & Webhook Marketplace ───────────────────────────
    from backend.routes.developer import developer_bp
    app.register_blueprint(developer_bp)
    log.debug("Blueprint registered: developer")

    log.info("All blueprints registered successfully.")
