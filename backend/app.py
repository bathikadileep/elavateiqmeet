"""
ElevateIQ Meeting Platform — Application Factory
=================================================
Usage:
    # Development
    from backend.app import create_app
    app = create_app("development")

    # Testing
    app = create_app("testing")

    # Production (via wsgi.py)
    app = create_app("production")

Flask-Migrate CLI:
    set FLASK_APP=backend.wsgi
    flask db init
    flask db migrate -m "initial schema"
    flask db upgrade
"""

import os
import sys

# Ensure project root is in sys.path when running from backend directory
_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import logging
from flask import Flask

log = logging.getLogger("elevateiq.app")


def create_app(config_name: str = None) -> Flask:
    """
    Application Factory.

    Args:
        config_name: One of "development", "testing", "production", or "default".
                     Falls back to the FLASK_ENV environment variable, then "development".

    Returns:
        Configured Flask application instance.
    """
    # ── Resolve config environment ────────────────────────────────────────────
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    from backend.config import config_registry
    config_class = config_registry.get(config_name, config_registry["default"])

    # ── Create Flask app ──────────────────────────────────────────────────────
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    # ── Step 1: Logging (must be first so all subsequent steps can log) ───────
    from backend.core.logging import setup_logging
    setup_logging(app)
    log.info("Starting ElevateIQ | env=%s | config=%s", config_name, config_class.__name__)

    # ── Step 2: Flask Extensions ──────────────────────────────────────────────
    _init_extensions(app)

    # ── Step 3: JWT Callbacks ─────────────────────────────────────────────────
    from backend.core.jwt_callbacks import register_jwt_callbacks
    from backend.extensions import jwt
    register_jwt_callbacks(jwt)

    # ── Step 4: Error Handlers ────────────────────────────────────────────────
    from backend.core.errors import register_error_handlers
    register_error_handlers(app)

    # ── Step 5: Blueprints ────────────────────────────────────────────────────
    from backend.routes.registry import register_blueprints
    register_blueprints(app)

    # ── Step 6: Request Lifecycle Hooks ───────────────────────────────────────
    _register_request_hooks(app)

    # ── Step 7: Directory Bootstrap ───────────────────────────────────────────
    _bootstrap_directories(app)

    log.info("Application ready. PID=%d", os.getpid())
    return app


# ── Private Helpers ────────────────────────────────────────────────────────────

def _init_extensions(app: Flask) -> None:
    """Bind all Flask extensions to the app instance."""
    from backend.extensions import db, migrate, bcrypt, jwt, cors, socketio

    db.init_app(app)

    # Flask-Migrate: bind to db and locate the migrations directory
    migrate.init_app(app, db, directory=app.config.get("MIGRATE_DIR", "migrations"))

    bcrypt.init_app(app)
    jwt.init_app(app)

    # CORS: credentials-aware configuration (required for HttpOnly cookie auth)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
    )

    # Socket.IO: allow all CORS origins
    socketio.init_app(
        app,
        cors_allowed_origins="*",
    )

    from backend.sockets import init_sockets
    init_sockets(socketio)

    log.debug("Extensions initialized: db, migrate, bcrypt, jwt, cors, socketio")


def _register_request_hooks(app: Flask) -> None:
    """Attach before/after request lifecycle logging and cleanup hooks."""

    @app.before_request
    def log_request_start():
        from flask import request, g
        import time
        g.start_time = time.monotonic()
        log.debug(
            "Request started",
            extra={"method": request.method, "path": request.path},
        )

    @app.after_request
    def log_request_end(response):
        from flask import request, g
        import time
        duration_ms = round((time.monotonic() - g.get("start_time", 0)) * 1000, 2)
        log.info(
            "Request completed",
            extra={
                "method":   request.method,
                "path":     request.path,
                "status":   response.status_code,
                "duration": f"{duration_ms}ms",
            },
        )
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        return response

    @app.teardown_appcontext
    def shutdown_db_session(exc):
        """Ensure the SQLAlchemy session is always properly closed."""
        from backend.extensions import db
        db.session.remove()

    log.debug("Request lifecycle hooks registered.")


def _bootstrap_directories(app: Flask) -> None:
    """Create required filesystem directories if they don't exist."""
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    subdirs = [
        upload_folder,
        os.path.join(upload_folder, "avatars"),
        os.path.join(upload_folder, "attachments"),
        os.path.join(upload_folder, "recordings"),
    ]
    for d in subdirs:
        os.makedirs(d, exist_ok=True)

    log.debug("Upload directories bootstrapped at: %s", upload_folder)


# ── Development Runner ────────────────────────────────────────────────────────

if __name__ == "__main__":
    from backend.extensions import socketio
    _app = create_app("development")
    socketio.run(
        _app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True,
        allow_unsafe_werkzeug=True,
        use_reloader=True,
    )
