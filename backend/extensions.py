"""
ElevateIQ — Flask Extension Singletons
=======================================
All extensions are instantiated WITHOUT an app object here
and bound to the app inside create_app() via the init_app() pattern.
This prevents circular import issues and allows the same extensions
to be shared across the app factory and test factories.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate    import Migrate
from flask_bcrypt     import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors       import CORS
from flask_socketio   import SocketIO

# ── Database ─────────────────────────────────────────────────────────────────
db      = SQLAlchemy()
migrate = Migrate()

# ── Security ──────────────────────────────────────────────────────────────────
bcrypt = Bcrypt()
jwt    = JWTManager()

# ── Cross-Origin & Real-time ──────────────────────────────────────────────────
cors     = CORS()
socketio = SocketIO(
    async_mode="threading",   # Compatible with Python 3.14 on Windows (no eventlet monkey-patch)
    cors_allowed_origins="*", # Overridden inside create_app() with config values
    manage_session=False,     # Flask 3.1 compatibility (session is read-only property on RequestContext)
    logger=False,
    engineio_logger=False,
)
