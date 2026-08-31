"""
ElevateIQ — Production WSGI Entry Point
=========================================
Used by Gunicorn, uWSGI, and the Flask CLI (flask db / flask shell).

Gunicorn launch example:
    gunicorn "backend.wsgi:application" \
        --workers 4 \
        --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
        --bind 0.0.0.0:5000 \
        --access-logfile - \
        --error-logfile -

Flask CLI usage:
    set FLASK_APP=backend.wsgi
    flask db init
    flask db migrate -m "initial migration"
    flask db upgrade
    flask shell
"""

import os
import sys

# Ensure both repo root and backend directory are in sys.path
_current_dir = os.path.abspath(os.path.dirname(__file__))
_parent_dir = os.path.abspath(os.path.join(_current_dir, ".."))
for p in (_parent_dir, _current_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.app import create_app
    from backend.extensions import socketio
except ImportError:
    from app import create_app
    from extensions import socketio

# Determine environment: production by default, override via FLASK_ENV
_env = os.getenv("FLASK_ENV", "production")

# Create the app — used by Gunicorn as the WSGI callable
app = create_app(_env)

# socketio.run() wraps the WSGI app; expose both for compatibility
application = socketio.wsgi_app if hasattr(socketio, "wsgi_app") else app
