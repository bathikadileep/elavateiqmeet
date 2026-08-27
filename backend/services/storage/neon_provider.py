"""
ElevateIQ — Neon PostgreSQL BYTEA Storage Provider
===================================================
Stores binary file data directly inside Neon PostgreSQL database tables.
"""

import uuid
import logging
from typing import Optional, Dict, Any, BinaryIO
from backend.services.storage.base import BaseStorageProvider
from backend.extensions import db

log = logging.getLogger("elevateiq.storage.neon")


class NeonStorageFile(db.Model):
    __tablename__ = "neon_storage_files"

    id           = db.Column(db.String(50), primary_key=True)
    storage_path = db.Column(db.String(500), unique=True, nullable=False, index=True)
    filename     = db.Column(db.String(255), nullable=False)
    mime_type    = db.Column(db.String(127), nullable=False)
    binary_data  = db.Column(db.LargeBinary, nullable=False)
    size_bytes   = db.Column(db.BigInteger, nullable=False)
    created_at   = db.Column(db.DateTime, default=db.func.now())


class NeonStorageProvider(BaseStorageProvider):

    def upload_file(self, file_obj: BinaryIO, filename: str, mime_type: str, folder: str = "general") -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1] if hasattr(os, 'path') else ''
        stored_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = f"{folder}/{stored_name}"

        file_obj.seek(0)
        data = file_obj.read()

        record = NeonStorageFile(
            id=uuid.uuid4().hex,
            storage_path=storage_path,
            filename=filename,
            mime_type=mime_type,
            binary_data=data,
            size_bytes=len(data)
        )
        db.session.add(record)
        db.session.commit()

        log.info("NeonStorageProvider: Stored %s in DB (%d bytes)", storage_path, len(data))
        return {
            "stored_name": stored_name,
            "storage_path": storage_path,
            "download_url": f"/api/files/download/{storage_path}",
            "size_bytes": len(data),
            "provider": "neon"
        }

    def download_file(self, storage_path: str) -> Optional[bytes]:
        record = NeonStorageFile.query.filter_by(storage_path=storage_path).first()
        if record:
            return record.binary_data
        return None

    def get_url(self, storage_path: str) -> str:
        return f"/api/files/download/{storage_path}"

    def delete_file(self, storage_path: str) -> bool:
        record = NeonStorageFile.query.filter_by(storage_path=storage_path).first()
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False

    def file_exists(self, storage_path: str) -> bool:
        return NeonStorageFile.query.filter_by(storage_path=storage_path).count() > 0
