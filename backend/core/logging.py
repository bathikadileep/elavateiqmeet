"""
ElevateIQ — Structured Logging Setup
======================================
Configures two handlers:
  1. StreamHandler   → colored output to stdout (always on)
  2. RotatingFileHandler → JSON-formatted log files (when LOG_TO_FILE=True)

JSON log format example:
  {
    "timestamp": "2026-08-22T10:30:00.000Z",
    "level": "INFO",
    "logger": "elevateiq.app",
    "message": "Request completed",
    "module": "app",
    "funcName": "health",
    "lineno": 42
  }
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from flask import Flask


# ── JSON Formatter ────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    RESERVED_ATTRS = {
        "args", "asctime", "created", "exc_info", "exc_text",
        "filename", "funcName", "id", "levelname", "levelno",
        "lineno", "module", "msecs", "message", "msg", "name",
        "pathname", "process", "processName", "relativeCreated",
        "stack_info", "thread", "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        log_dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
                                 .strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.message,
            "module":    record.module,
            "func":      record.funcName,
            "line":      record.lineno,
        }

        # Attach exception info if present
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)

        # Attach any extra fields passed via logger.info("msg", extra={...})
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                log_dict[key] = value

        return json.dumps(log_dict, default=str)


# ── Console Formatter ─────────────────────────────────────────────────────────

CONSOLE_COLORS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
}
RESET = "\033[0m"

class ColorConsoleFormatter(logging.Formatter):
    """Human-readable colored console formatter (%-style)."""

    BASE_FMT = "%(color)s[%(levelname)-8s]%(reset)s %(asctime)s | %(name)s | %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        color = CONSOLE_COLORS.get(record.levelname, "")
        record.color = color
        record.reset = RESET
        formatter = logging.Formatter(self.BASE_FMT, datefmt="%H:%M:%S")
        return formatter.format(record)


# ── Setup Function ────────────────────────────────────────────────────────────

def setup_logging(app: Flask) -> None:
    """
    Configure application-wide logging.
    Called once inside create_app() after app config is loaded.
    """
    log_level_name = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level      = getattr(logging, log_level_name, logging.INFO)
    log_to_file    = app.config.get("LOG_TO_FILE", False)
    log_dir        = app.config.get("LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "logs"))

    # Root logger setup — controls everything under the "backend" namespace
    root_logger = logging.getLogger("elevateiq")
    root_logger.setLevel(log_level)

    # Prevent duplicate handlers on hot-reload
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # ── Handler 1: Console (always active) ───────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColorConsoleFormatter())
    root_logger.addHandler(console_handler)

    # ── Handler 2: Rotating JSON file (production / LOG_TO_FILE=True) ────────
    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "elevateiq.log")

        file_handler = logging.handlers.RotatingFileHandler(
            filename    = log_file,
            maxBytes    = 10 * 1024 * 1024,   # 10 MB per file
            backupCount = 5,                   # keep last 5 rotated files
            encoding    = "utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # ── Suppress noisy third-party loggers ────────────────────────────────────
    for noisy in ("werkzeug", "socketio", "engineio", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    app.logger.handlers = root_logger.handlers
    app.logger.setLevel(log_level)
    app.logger.propagate = False

    root_logger.info(
        "Logging initialized",
        extra={"level": log_level_name, "file": log_to_file},
    )
