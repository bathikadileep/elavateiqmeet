"""
ElevateIQ Meeting Platform — Backend Configuration
====================================================
Multi-environment configuration hierarchy:
    Config (base) → DevelopmentConfig / ProductionConfig / TestingConfig

Loaded via create_app(config_name="development") or FLASK_ENV env var.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env from the same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _parse_db_url(raw: str) -> str:
    """
    Normalize any Postgres URL variant to use the pg8000 driver.
    Strips sslmode/channel_binding from the URL query string — pg8000
    requires these to be passed via connect_args instead.
    """
    import re as _re
    if not raw:
        return ""
    url = raw.strip()
    for prefix, replacement in [
        ("postgresql+pg8000://", "postgresql+pg8000://"),
        ("postgresql://",        "postgresql+pg8000://"),
        ("postgres://",          "postgresql+pg8000://"),
    ]:
        if url.startswith(prefix):
            url = url.replace(prefix, replacement, 1)
            break

    # Strip unsupported query params (sslmode, channel_binding)
    # pg8000 uses ssl_context=True via connect_args, not URL params
    url = _re.sub(r'\?.*$', '', url)
    return url.strip()


# ---------------------------------------------------------------------------
# Base Config — shared across all environments
# ---------------------------------------------------------------------------

class Config:
    # ── Flask Core ──────────────────────────────────────────────────────────
    SECRET_KEY      = os.getenv("SECRET_KEY", "change-me-in-production-!elevateiq").strip()
    APP_NAME        = "ElevateIQ Meeting Platform"
    API_VERSION     = "v1"
    API_PREFIX      = "/api/v1"

    # ── SQLAlchemy ──────────────────────────────────────────────────────────
    _raw_db_url = os.getenv("DATABASE_URL", "").strip()
    if _raw_db_url:
        SQLALCHEMY_DATABASE_URI = _parse_db_url(_raw_db_url)
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'elevateiq.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,       # reconnect on stale connections
        "pool_recycle":  300,        # recycle connections every 5 min
        "pool_size":     5,
        "max_overflow":  10,
        "connect_args":  {"ssl_context": True},   # pg8000 SSL for Neon (replaces sslmode=require in URL)
    }

    # ── Flask-Migrate ───────────────────────────────────────────────────────
    MIGRATE_DIR = os.path.join(BASE_DIR, "migrations")

    # ── JWT ─────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY              = os.getenv("JWT_SECRET_KEY", "change-jwt-secret-in-production!")
    JWT_TOKEN_LOCATION          = ["cookies", "headers"]
    JWT_ACCESS_COOKIE_PATH      = "/"
    JWT_REFRESH_COOKIE_PATH     = f"/api/v1/auth/refresh"
    JWT_COOKIE_SECURE           = False
    JWT_COOKIE_CSRF_PROTECT     = False
    JWT_COOKIE_SAMESITE         = "Lax"
    JWT_ACCESS_TOKEN_EXPIRES    = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES   = timedelta(days=7)

    # ── CORS ────────────────────────────────────────────────────────────────
    CORS_ALLOWED_ORIGINS = os.getenv(
        "CORS_ALLOWED_ORIGINS", "*"
    ).split(",")

    # ── File Uploads ─────────────────────────────────────────────────────────
    UPLOAD_FOLDER       = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH  = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))  # 5 MB default
    ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR    = os.path.join(BASE_DIR, "logs")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() in ("true", "1", "yes")

    # ── Pagination ───────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE     = int(os.getenv("MAX_PAGE_SIZE", "100"))


# ---------------------------------------------------------------------------
# Development Config
# ---------------------------------------------------------------------------

class DevelopmentConfig(Config):
    DEBUG       = True
    TESTING     = False
    LOG_LEVEL   = "DEBUG"
    LOG_TO_FILE = False   # Console-only in dev for speed

    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "echo": False,   # Set True to log all SQL queries during dev
    }


# ---------------------------------------------------------------------------
# Testing Config — uses in-memory SQLite, no file side-effects
# ---------------------------------------------------------------------------

class TestingConfig(Config):
    DEBUG    = True
    TESTING  = True

    SQLALCHEMY_DATABASE_URI   = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}   # No pooling or SSL for in-memory SQLite

    JWT_COOKIE_SECURE   = False
    LOG_TO_FILE         = False
    WTF_CSRF_ENABLED    = False


# ---------------------------------------------------------------------------
# Production Config
# ---------------------------------------------------------------------------

class ProductionConfig(Config):
    DEBUG       = False
    TESTING     = False
    LOG_LEVEL   = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "False").lower() in ("true", "1", "yes")

    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "True").lower() in ("true", "1", "yes")

    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size":    10,
        "max_overflow": 20,
    }


# ---------------------------------------------------------------------------
# Config registry — used by create_app()
# ---------------------------------------------------------------------------

config_registry = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
