"""
ElevateIQ — Abstract Base Storage Provider Interface
======================================================
Defines standard interface for all pluggable storage drivers (Local, Neon DB, AWS S3 / Cloudflare R2).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO


class BaseStorageProvider(ABC):
    """Abstract base class for all pluggable storage drivers."""

    @abstractmethod
    def upload_file(self, file_obj: BinaryIO, filename: str, mime_type: str, folder: str = "general") -> Dict[str, Any]:
        """
        Upload binary data to storage.
        Returns metadata dict containing: stored_name, storage_path, download_url, size_bytes.
        """
        pass

    @abstractmethod
    def download_file(self, storage_path: str) -> Optional[bytes]:
        """Download binary data from storage by path."""
        pass

    @abstractmethod
    def get_url(self, storage_path: str) -> str:
        """Get accessible download URL for a stored file."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Delete stored file by path. Returns True if deleted."""
        pass

    @abstractmethod
    def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in storage."""
        pass
