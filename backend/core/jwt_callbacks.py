"""
ElevateIQ — JWT Callbacks & Identity Loader
=============================================
Registers all Flask-JWT-Extended callback hooks:
  - Identity loader   (token → user object)
  - Error responses   (expired, invalid, missing, revoked tokens)
  - Additional claims (embed role info in token payload)

All JWT error responses match the global error envelope format.
"""

import logging
from flask import jsonify
from flask_jwt_extended import JWTManager

log = logging.getLogger("elevateiq.jwt")


def _jwt_error(code: str, message: str, status: int):
    """Consistent JWT error response matching the global error envelope."""
    return jsonify({
        "error": {
            "code":    code,
            "message": message,
            "status":  status,
        }
    }), status


def register_jwt_callbacks(jwt: JWTManager) -> None:
    """
    Register all JWT-Extended loader and error callbacks.
    Called once inside create_app() after jwt.init_app(app).
    """

    # ── Identity Loader ───────────────────────────────────────────────────────
    @jwt.user_identity_loader
    def user_identity_loader(user):
        """
        Define what gets stored as the JWT 'sub' (subject) claim.
        We store the string user ID.
        """
        if hasattr(user, "id"):
            return str(user.id)
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_loader(_jwt_header, jwt_data):
        """
        Reload the full User object from the database on every protected request.
        Populates flask_jwt_extended.current_user automatically.
        """
        from backend.models.models import User
        user_id = jwt_data.get("sub")
        if not user_id:
            return None
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    # ── Additional Claims Loader ──────────────────────────────────────────────
    @jwt.additional_claims_loader
    def add_claims(user):
        """
        Embed lightweight metadata into the JWT payload so the frontend
        doesn't need an extra round-trip to determine the user's role.
        """
        if hasattr(user, "roles") and user.roles:
            role_names = [r.name for r in user.roles]
        else:
            role_names = []
        return {
            "roles":        role_names,
            "display_name": getattr(user, "display_name", ""),
        }

    # ── Token Error Callbacks ─────────────────────────────────────────────────

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_data):
        log.debug("JWT expired token presented.")
        return _jwt_error(
            "TOKEN_EXPIRED",
            "Your session has expired. Please log in again.",
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(reason: str):
        log.warning("JWT invalid token: %s", reason)
        return _jwt_error(
            "TOKEN_INVALID",
            f"Token validation failed: {reason}",
            422,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(reason: str):
        log.debug("JWT missing token: %s", reason)
        return _jwt_error(
            "TOKEN_MISSING",
            "Authentication token is missing. Please log in.",
            401,
        )

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_callback(_jwt_header, _jwt_data):
        return _jwt_error(
            "TOKEN_NOT_FRESH",
            "A fresh login is required to perform this action.",
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_data):
        log.warning("JWT revoked token presented.")
        return _jwt_error(
            "TOKEN_REVOKED",
            "This token has been revoked. Please log in again.",
            401,
        )

    @jwt.user_lookup_error_loader
    def user_lookup_error_callback(_jwt_header, jwt_data):
        uid = jwt_data.get("sub")
        log.warning("JWT user lookup failed for sub=%s", uid)
        return _jwt_error(
            "USER_NOT_FOUND",
            "The account associated with this token no longer exists.",
            401,
        )

    log.info("JWT callbacks registered.")
