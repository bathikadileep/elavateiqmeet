"""
ElevateIQ — Health & Diagnostics Blueprint
===========================================
Provides system health and readiness endpoints.
These routes are intentionally NOT protected by JWT authentication
so they can be polled by load balancers, Docker health checks, and
monitoring systems without credentials.
"""

import logging
from flask import Blueprint, jsonify, current_app
from backend.extensions import db

log = logging.getLogger("elevateiq.health")

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def index_welcome():
    """
    GET /
    Root welcome endpoint for the ElevateIQ API server.
    """
    return jsonify({
        "service": current_app.config.get("APP_NAME", "ElevateIQ Meeting Platform"),
        "status": "online",
        "version": current_app.config.get("API_VERSION", "v1"),
        "health_check": "/api/v1/health",
        "documentation": "/api/v1/ready",
    }), 200


@health_bp.route("/api/v1/health", methods=["GET"])
def liveness():
    """
    GET /api/v1/health
    Liveness probe — confirms the Flask process is alive.
    Does NOT touch the database. Suitable for Docker HEALTHCHECK.
    """
    return jsonify({
        "status": "ok",
        "service": current_app.config.get("APP_NAME", "ElevateIQ"),
        "version": current_app.config.get("API_VERSION", "v1"),
    }), 200


@health_bp.route("/api/v1/ready", methods=["GET"])
def readiness():
    """
    GET /api/v1/ready
    Readiness probe — confirms the app + database connection are healthy.
    Use this for Kubernetes readiness gates or pre-warm checks.
    """
    db_ok = False
    try:
        db.session.execute(db.select(1))
        db_ok = True
    except Exception as exc:
        log.error("Readiness check failed — DB unreachable: %s", exc)

    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "ready" if db_ok else "degraded",
        "service": current_app.config.get("APP_NAME", "ElevateIQ"),
        "database": "connected" if db_ok else "unreachable",
    }), status_code
