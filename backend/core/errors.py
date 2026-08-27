"""
ElevateIQ — Centralized Error Handling
========================================
Provides:
  1. Custom application exception hierarchy
  2. Flask error handler registration function
  3. Consistent JSON error response format across all error types

All error responses follow the envelope:
  {
    "error": {
      "code":    "NOT_FOUND",
      "message": "The requested resource was not found.",
      "status":  404,
      "details": {}   # optional
    }
  }
"""

import logging
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger("elevateiq.errors")


# ── Error Response Builder ────────────────────────────────────────────────────

def _error_response(code: str, message: str, status: int, details: dict = None):
    payload = {
        "error": {
            "code":    code,
            "message": message,
            "status":  status,
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status


# ── Custom Exception Hierarchy ────────────────────────────────────────────────

class ElevateIQError(Exception):
    """Base exception for all ElevateIQ application errors."""
    status_code = 500
    error_code  = "INTERNAL_ERROR"
    message     = "An unexpected error occurred."

    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}

    def to_response(self):
        return _error_response(self.error_code, self.message, self.status_code, self.details)


class BadRequestError(ElevateIQError):
    status_code = 400
    error_code  = "BAD_REQUEST"
    message     = "The request is invalid or malformed."


class AuthenticationError(ElevateIQError):
    status_code = 401
    error_code  = "UNAUTHENTICATED"
    message     = "Authentication is required to access this resource."


class AuthorizationError(ElevateIQError):
    status_code = 403
    error_code  = "FORBIDDEN"
    message     = "You do not have permission to perform this action."


class NotFoundError(ElevateIQError):
    status_code = 404
    error_code  = "NOT_FOUND"
    message     = "The requested resource was not found."


class ConflictError(ElevateIQError):
    status_code = 409
    error_code  = "CONFLICT"
    message     = "The resource already exists or conflicts with an existing record."


class UnprocessableError(ElevateIQError):
    status_code = 422
    error_code  = "UNPROCESSABLE_ENTITY"
    message     = "The request data failed validation."


class RateLimitError(ElevateIQError):
    status_code = 429
    error_code  = "RATE_LIMITED"
    message     = "Too many requests. Please slow down."


class ServiceUnavailableError(ElevateIQError):
    status_code = 503
    error_code  = "SERVICE_UNAVAILABLE"
    message     = "The service is temporarily unavailable."


# ── Handler Registration ──────────────────────────────────────────────────────

def register_error_handlers(app: Flask) -> None:
    """
    Attach all error handlers to the Flask application.
    Called once inside create_app().
    """

    # ── Custom ElevateIQ exceptions ───────────────────────────────────────────
    @app.errorhandler(ElevateIQError)
    def handle_elevateiq_error(exc: ElevateIQError):
        log.warning(
            "Application error",
            extra={"code": exc.error_code, "status": exc.status_code, "path": request.path},
        )
        return exc.to_response()

    # ── Werkzeug / Flask built-in HTTP exceptions ─────────────────────────────
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        log.warning(
            "HTTP exception",
            extra={"status": exc.code, "name": exc.name, "path": request.path},
        )
        return _error_response(
            code    = exc.name.upper().replace(" ", "_"),
            message = exc.description,
            status  = exc.code,
        )

    # ── 400 Bad Request ───────────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(exc):
        return _error_response("BAD_REQUEST", "The request is malformed or missing required fields.", 400)

    # ── 401 Unauthorized ──────────────────────────────────────────────────────
    @app.errorhandler(401)
    def unauthorized(exc):
        return _error_response("UNAUTHENTICATED", "Authentication credentials are required.", 401)

    # ── 403 Forbidden ─────────────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(exc):
        return _error_response("FORBIDDEN", "You do not have permission to access this resource.", 403)

    # ── 404 Not Found ─────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(exc):
        return _error_response("NOT_FOUND", f"The path '{request.path}' was not found.", 404)

    # ── 405 Method Not Allowed ────────────────────────────────────────────────
    @app.errorhandler(405)
    def method_not_allowed(exc):
        return _error_response(
            "METHOD_NOT_ALLOWED",
            f"Method '{request.method}' is not allowed on this endpoint.",
            405,
        )

    # ── 409 Conflict ──────────────────────────────────────────────────────────
    @app.errorhandler(409)
    def conflict(exc):
        return _error_response("CONFLICT", "Resource already exists.", 409)

    # ── 413 Payload Too Large ────────────────────────────────────────────────
    @app.errorhandler(413)
    def payload_too_large(exc):
        return _error_response("PAYLOAD_TOO_LARGE", "The uploaded file exceeds the maximum allowed size.", 413)

    # ── 422 Unprocessable Entity ──────────────────────────────────────────────
    @app.errorhandler(422)
    def unprocessable(exc):
        return _error_response("UNPROCESSABLE_ENTITY", "The request data failed validation.", 422)

    # ── 429 Too Many Requests ────────────────────────────────────────────────
    @app.errorhandler(429)
    def rate_limited(exc):
        return _error_response("RATE_LIMITED", "Too many requests. Please try again later.", 429)

    # ── 500 Internal Server Error (catch-all) ────────────────────────────────
    @app.errorhandler(Exception)
    def internal_server_error(exc):
        # Log full traceback for unexpected errors
        log.exception(
            "Unhandled exception",
            extra={"path": request.path, "method": request.method},
        )
        # Never expose internal error details to clients in production
        if app.config.get("DEBUG"):
            msg = str(exc)
        else:
            msg = "An internal server error occurred. Please try again later."
        return _error_response("INTERNAL_ERROR", msg, 500)

    log.info("Error handlers registered.")
