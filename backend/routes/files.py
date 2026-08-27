"""
ElevateIQ — File Sharing & Upload Blueprint
=============================================
Endpoints:
  POST   /api/v1/files/upload           → Upload single file (Multipart Form)
  GET    /api/v1/files                  → List uploaded files (with meeting/user filter)
  GET    /api/v1/files/<file_id>/download → Download file as attachment
  GET    /api/v1/files/<file_id>/preview  → Serve file inline for preview
  DELETE /api/v1/files/<file_id>        → Soft delete file record & disk file
"""

import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.models.models import File, User, Meeting
from backend.core.errors import (
    BadRequestError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)

log = logging.getLogger("elevateiq.files")

files_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")

# Allowed MIME type categories matching DB FileCategoryEnum
ALLOWED_CATEGORIES = {"avatar", "attachment", "recording", "transcript"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


def get_upload_directory():
    """Retrieve absolute upload directory path from config or create default."""
    folder = current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.root_path, "uploads")
    os.makedirs(folder, exist_ok=True)
    return folder


# ── 1. Upload File Endpoint ───────────────────────────────────────────────────

@files_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    """
    POST /api/v1/files/upload
    Form Data: file (FileStorage), meeting_id (optional), file_category (optional)
    """
    user_id = get_jwt_identity()

    if "file" not in request.files:
        raise BadRequestError("No file payload provided in request.")

    file_obj = request.files["file"]
    if not file_obj or file_obj.filename == "":
        raise BadRequestError("Empty file selected for upload.")

    meeting_id    = request.form.get("meeting_id")
    file_category = request.form.get("file_category", "attachment")

    if file_category not in ALLOWED_CATEGORIES:
        file_category = "attachment"

    # Verify meeting exists if specified
    if meeting_id:
        meeting = db.session.get(Meeting, meeting_id)
        if not meeting or meeting.is_deleted:
            raise NotFoundError("Associated meeting not found.")

    original_name = secure_filename(file_obj.filename) or "unnamed_file"
    file_ext      = os.path.splitext(original_name)[1]
    stored_name   = f"{uuid.uuid4().hex}{file_ext}"
    upload_dir    = get_upload_directory()
    storage_path  = os.path.join(upload_dir, stored_name)

    # Save to disk & calculate SHA-256 checksum
    hasher = hashlib.sha256()
    bytes_read = 0

    try:
        with open(storage_path, "wb") as f:
            while chunk := file_obj.read(8192):
                bytes_read += len(chunk)
                if bytes_read > MAX_FILE_SIZE_BYTES:
                    f.close()
                    os.remove(storage_path)
                    raise BadRequestError("File size exceeds 50MB maximum limit.")
                f.write(chunk)
                hasher.update(chunk)
    except Exception as exc:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if isinstance(exc, BadRequestError):
            raise exc
        log.error("Failed writing file to disk: %s", exc)
        raise BadRequestError("Failed to store file on server disk.")

    mime_type = file_obj.mimetype or "application/octet-stream"
    checksum = hasher.hexdigest()

    new_file = File(
        uploader_id=user_id,
        meeting_id=meeting_id if meeting_id else None,
        file_category=file_category,
        original_name=original_name,
        stored_name=stored_name,
        storage_path=storage_path,
        mime_type=mime_type,
        size_bytes=bytes_read,
        checksum_sha256=checksum,
    )
    db.session.add(new_file)
    db.session.commit()

    log.info("File uploaded successfully: id=%s name=%s size=%d", new_file.id, original_name, bytes_read)
    return jsonify({
        "message": "File uploaded successfully.",
        "file": new_file.to_dict(),
    }), 201


# ── 2. List Files Endpoint ────────────────────────────────────────────────────

@files_bp.route("", methods=["GET"])
@jwt_required()
def list_files():
    """
    GET /api/v1/files?meeting_id=...&category=...
    List uploaded files.
    """
    user_id    = get_jwt_identity()
    meeting_id = request.args.get("meeting_id")
    category   = request.args.get("category")

    query = db.select(File).where(File.is_deleted == False)

    if meeting_id:
        query = query.where(File.meeting_id == meeting_id)
    else:
        # Default to user's uploaded files or room files
        query = query.where(File.uploader_id == user_id)

    if category and category in ALLOWED_CATEGORIES:
        query = query.where(File.file_category == category)

    query = query.order_by(File.created_at.desc())
    files = db.session.scalars(query).all()

    return jsonify({"files": [f.to_dict() for f in files]}), 200


# ── 3. Download File Endpoint ─────────────────────────────────────────────────

@files_bp.route("/<file_id>/download", methods=["GET"])
@jwt_required()
def download_file(file_id):
    """
    GET /api/v1/files/<file_id>/download
    Download file attachment.
    """
    file_record = db.session.get(File, file_id)
    if not file_record or file_record.is_deleted:
        raise NotFoundError("File not found.")

    upload_dir = get_upload_directory()
    return send_from_directory(
        upload_dir,
        file_record.stored_name,
        as_attachment=True,
        download_name=file_record.original_name,
        mimetype=file_record.mime_type,
    )


# ── 4. Preview File Endpoint ──────────────────────────────────────────────────

@files_bp.route("/<file_id>/preview", methods=["GET"])
@jwt_required()
def preview_file(file_id):
    """
    GET /api/v1/files/<file_id>/preview
    Serve file inline for browser rendering/preview.
    """
    file_record = db.session.get(File, file_id)
    if not file_record or file_record.is_deleted:
        raise NotFoundError("File not found.")

    upload_dir = get_upload_directory()
    return send_from_directory(
        upload_dir,
        file_record.stored_name,
        as_attachment=False,
        download_name=file_record.original_name,
        mimetype=file_record.mime_type,
    )


# ── 5. Delete File Endpoint ───────────────────────────────────────────────────

@files_bp.route("/<file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    """
    DELETE /api/v1/files/<file_id>
    Delete file record & remove from disk.
    """
    user_id = get_jwt_identity()
    file_record = db.session.get(File, file_id)

    if not file_record or file_record.is_deleted:
        raise NotFoundError("File not found.")

    # Authorization gate: uploader or super admin
    user = db.session.get(User, user_id)
    is_admin = False
    if user:
        is_admin = any(r.role_name == "super_admin" for r in user.roles)

    if file_record.uploader_id != user_id and not is_admin:
        raise AuthorizationError("Only the uploader or an administrator can delete this file.")

    # Remove disk file if present
    if os.path.exists(file_record.storage_path):
        try:
            os.remove(file_record.storage_path)
        except Exception as exc:
            log.warning("Could not remove disk file: %s", exc)

    file_record.is_deleted = True
    file_record.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

    log.info("File deleted: id=%s by user_id=%s", file_id, user_id)
    return jsonify({"message": "File deleted successfully."}), 200
