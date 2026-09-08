"""
ElevateIQ — Local File Storage Provider
=======================================
Implements local disk file storage provider for avatars, attachments, and cloud recordings.
"""

import os
import shutil
import logging
from typing import Dict, Any, Optional
from backend.services.storage.base import BaseStorageProvider

log = logging.getLogger("elevateiq.storage.local")


class LocalStorageProvider(BaseStorageProvider):
    """Local Filesystem Storage Provider."""

    def __init__(self, base_directory: str = "uploads"):
        self.base_directory = base_directory
        os.makedirs(self.base_directory, exist_ok=True)

    def upload_file(self, file_obj: Any, filename: str, mime_type: str = "application/octet-stream", folder: str = "general") -> Dict[str, Any]:
        """Save file bytes or stream to local disk directory."""
        if isinstance(file_obj, bytes):
            file_bytes = file_obj
        elif hasattr(file_obj, "read"):
            file_bytes = file_obj.read()
        else:
            file_bytes = str(file_obj).encode("utf-8")

        target_dir = os.path.join(self.base_directory, folder)
        full_path = os.path.join(target_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        log.info("Saved local storage file: %s (%d bytes)", full_path, len(file_bytes))
        storage_path = f"{folder}/{filename}"
        return {
            "stored_name": filename,
            "storage_path": storage_path,
            "download_url": f"/uploads/{storage_path}",
            "size_bytes": len(file_bytes),
        }

    def download_file(self, storage_path: str) -> Optional[bytes]:
        """Read file bytes from local disk."""
        full_path = os.path.join(self.base_directory, storage_path.lstrip("/\\"))
        if not os.path.exists(full_path):
            return None

        with open(full_path, "rb") as f:
            return f.read()

    def get_url(self, storage_path: str) -> str:
        """Get accessible download URL for local file."""
        return f"/uploads/{storage_path.lstrip('/\\')}"

    def delete_file(self, storage_path: str) -> bool:
        """Delete file from local disk."""
        full_path = os.path.join(self.base_directory, storage_path.lstrip("/\\"))
        if os.path.exists(full_path):
            os.remove(full_path)
            log.info("Deleted local storage file: %s", full_path)
            return True
        return False

    def file_exists(self, storage_path: str) -> bool:
        """Check if file exists on local disk."""
        full_path = os.path.join(self.base_directory, storage_path.lstrip("/\\"))
        return os.path.exists(full_path)

