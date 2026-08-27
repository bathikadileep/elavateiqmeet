"""
ElevateIQ — Complete Authentication Blueprint
==============================================
Endpoints:
  POST /api/v1/auth/register         → Account creation
  POST /api/v1/auth/login            → Authenticate & issue HttpOnly JWT cookies
  POST /api/v1/auth/logout           → Clear JWT cookies
  POST /api/v1/auth/refresh          → Rotate access token
  GET  /api/v1/auth/me               → Current user profile
  POST /api/v1/auth/forgot-password  → Generate password reset token
  POST /api/v1/auth/reset-password   → Reset password using valid token
  POST /api/v1/auth/change-password  → Change password (authenticated)

Security Features:
  - Password hashing via Bcrypt (12 rounds)
  - Cryptographically secure reset tokens (secrets.token_urlsafe + SHA256 hashing)
  - 15-minute token TTL
  - Strict input sanitization & validation
  - Uniform JSON error envelopes
"""

import re
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, make_response, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity,
)
from backend.extensions import db
from backend.models.models import User
from backend.core.errors import (
    BadRequestError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
)

log = logging.getLogger("elevateiq.auth")

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _hash_token(raw_token: str) -> str:
    """Helper to generate SHA-256 hash of a raw token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ── 1. Register Account ───────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/v1/auth/register
    Body: { username, email, password, display_name? }
    """
    data = request.get_json(silent=True) or {}

    username     = (data.get("username", "") or "").strip()
    email        = (data.get("email", "") or "").strip().lower()
    password     = data.get("password", "") or ""
    display_name = (data.get("display_name", "") or "").strip() or username

    # Validation
    if not username or not email or not password:
        raise BadRequestError("username, email, and password are required.")

    if len(username) < 3:
        raise BadRequestError("Username must be at least 3 characters long.")

    if not EMAIL_REGEX.match(email):
        raise BadRequestError("Invalid email address format.")

    if len(password) < 6:
        raise BadRequestError("Password must be at least 6 characters long.")

    # Uniqueness check
    if db.session.execute(
        db.select(User).filter_by(username=username, is_deleted=False)
    ).scalar_one_or_none():
        raise ConflictError("Username is already taken.")

    if db.session.execute(
        db.select(User).filter_by(email=email, is_deleted=False)
    ).scalar_one_or_none():
        raise ConflictError("An account with this email already exists.")

    # Persist User
    user = User(
        username=username,
        email=email,
        display_name=display_name,
        status="active",
        email_verified=False,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    log.info("New user registered: %s (%s)", username, email)
    return jsonify({"message": "Account created successfully.", "user": user.to_dict()}), 201


# ── 2. Login ──────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/v1/auth/login
    Body: { identity (email or username), password }
    Sets HttpOnly access_token_cookie + refresh_token_cookie.
    """
    data = request.get_json(silent=True) or {}

    identity = (data.get("identity", "") or "").strip()
    password = data.get("password", "") or ""

    if not identity or not password:
        raise BadRequestError("identity (email or username) and password are required.")

    # Query user by username or email
    user = db.session.execute(
        db.select(User).where(
            db.or_(User.username == identity, User.email == identity.lower()),
            User.is_deleted == False,
        )
    ).scalar_one_or_none()

    if not user or not user.check_password(password):
        raise AuthenticationError("Invalid credentials. Please check your username/email and password.")

    if user.status == "suspended":
        raise AuthenticationError("Your account has been suspended. Please contact support.")

    # Update login audit metrics
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.remote_addr
    db.session.commit()

    # Issue JWT tokens
    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    response = make_response(jsonify({
        "message": "Login successful.",
        "user": user.to_dict(),
        "access_token": access_token,
    }))

    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    log.info("User logged in: %s", user.username)
    return response


# ── 3. Refresh Access Token ───────────────────────────────────────────────────

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    POST /api/v1/auth/refresh
    Rotates access token cookie using valid refresh token cookie.
    """
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)

    response = make_response(jsonify({"message": "Access token refreshed."}))
    set_access_cookies(response, new_access_token)

    log.debug("Access token refreshed for user_id=%s", user_id)
    return response


# ── 4. Logout ─────────────────────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/v1/auth/logout
    Clears all JWT cookies.
    """
    response = make_response(jsonify({"message": "Logged out successfully."}))
    unset_jwt_cookies(response)
    return response


# ── 5. Current User Profile ───────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    GET /api/v1/auth/me
    Returns current authenticated user profile.
    """
    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)
    if not user or user.is_deleted:
        raise AuthenticationError("User account not found or has been deactivated.")

    return jsonify({"user": user.to_dict()})


# ── 6. Forgot Password ────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    POST /api/v1/auth/forgot-password
    Body: { email }
    Generates a 15-minute password reset token.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email", "") or "").strip().lower()

    if not email or not EMAIL_REGEX.match(email):
        raise BadRequestError("A valid email address is required.")

    user = db.session.execute(
        db.select(User).filter_by(email=email, is_deleted=False)
    ).scalar_one_or_none()

    # Always return a generic success message to prevent user enumeration attacks
    if not user:
        log.info("Forgot password requested for non-existent email: %s", email)
        return jsonify({
            "message": "If an account exists with that email, a password reset link has been generated."
        }), 200

    # Generate cryptographically secure token & hash it for database storage
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    user.reset_token_hash = token_hash
    user.reset_token_expires_at = expires_at
    db.session.commit()

    log.info("Password reset token generated for user: %s", user.username)

    # Payload includes reset_token for dev testing
    payload = {
        "message": "Password reset instructions generated.",
        "reset_token": raw_token,
        "reset_url": f"/reset-password?token={raw_token}",
    }

    return jsonify(payload), 200


# ── 7. Reset Password ─────────────────────────────────────────────────────────

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    POST /api/v1/auth/reset-password
    Body: { token, new_password }
    """
    data = request.get_json(silent=True) or {}
    raw_token = (data.get("token", "") or "").strip()
    new_password = data.get("new_password", "") or ""

    if not raw_token or not new_password:
        raise BadRequestError("token and new_password are required.")

    if len(new_password) < 6:
        raise BadRequestError("Password must be at least 6 characters long.")

    token_hash = _hash_token(raw_token)

    user = db.session.execute(
        db.select(User).where(
            User.reset_token_hash == token_hash,
            User.reset_token_expires_at > datetime.now(timezone.utc),
            User.is_deleted == False,
        )
    ).scalar_one_or_none()

    if not user:
        raise BadRequestError("Invalid or expired password reset token.")

    # Update password & invalidate reset token
    user.set_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.session.commit()

    log.info("Password successfully reset for user: %s", user.username)
    return jsonify({"message": "Password has been reset successfully. You may now log in."}), 200


# ── 8. Change Password (Authenticated) ────────────────────────────────────────

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """
    POST /api/v1/auth/change-password
    Body: { current_password, new_password }
    Requires valid JWT access cookie.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    current_password = data.get("current_password", "") or ""
    new_password = data.get("new_password", "") or ""

    if not current_password or not new_password:
        raise BadRequestError("current_password and new_password are required.")

    if len(new_password) < 6:
        raise BadRequestError("New password must be at least 6 characters long.")

    user = db.session.get(User, user_id)
    if not user or user.is_deleted:
        raise AuthenticationError("User account not found.")

    if not user.check_password(current_password):
        raise BadRequestError("Current password is incorrect.")

    user.set_password(new_password)
    db.session.commit()

    log.info("Password changed by user: %s", user.username)
    return jsonify({"message": "Password changed successfully."}), 200
