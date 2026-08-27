"""
ElevateIQ — Local Disk Storage Provider Implementation
========================================================
Stores uploaded files and recordings directly on the local filesystem.
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any, BinaryIO
from backend.services.storage.base import BaseStorageProvider

log = logging.getLogger("elevateiq.storage.local")


class LocalStorageProvider(BaseStorageProvider):

    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_obj: BinaryIO, filename: str, mime_type: str, folder: str = "general") -> Dict[str, Any]:
        target_dir = os.path.join(self.base_dir, folder)
        os.makedirs(target_dir, exist_ok=True)

        ext = os.path.splitext(filename)[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = os.path.join(folder, stored_name)
        full_path = os.path.join(self.base_dir, storage_path)

        file_obj.seek(0)
        data = file_obj.read()
        with open(full_path, "wb") as f:
            f.write(data)

        size_bytes = len(data)
        download_url = f"/api/files/download/{storage_path.replace('\\', '/')}"

        log.info("LocalStorageProvider: Saved %s (%d bytes)", storage_path, size_bytes)
        return {
            "stored_name": stored_name,
            "storage_path": storage_path.replace("\\", "/"),
            "download_url": download_url,
            "size_bytes": size_bytes,
            "provider": "local"
        }

    def download_file(self, storage_path: str) -> Optional[bytes]:
        full_path = os.path.join(self.base_dir, storage_path.replace("/", os.sep))
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return f.read()
        return None

    def get_url(self, storage_path: str) -> str:
        return f"/api/files/download/{storage_path.replace('\\', '/')}"

    def delete_file(self, storage_path: str) -> bool:
        full_path = os.path.join(self.base_dir, storage_path.replace("/", os.sep))
        if os.path.exists(full_path):
            os.remove(full_path)
            log.info("LocalStorageProvider: Deleted %s", storage_path)
            return True
        return False

    def file_exists(self, storage_path: str) -> bool:
        full_path = os.path.join(self.base_dir, storage_path.replace("/", os.sep))
        return os.path.exists(full_path)
