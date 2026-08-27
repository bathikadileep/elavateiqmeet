"""
ElevateIQ — Storage Provider Factory
====================================
1-Click .env provider switching (STORAGE_PROVIDER=local | s3 | neon).
"""

import os
import logging
from backend.services.storage.base import BaseStorageProvider
from backend.services.storage.local_provider import LocalStorageProvider
from backend.services.storage.neon_provider import NeonStorageProvider
from backend.services.storage.s3_provider import S3StorageProvider

log = logging.getLogger("elevateiq.storage")

_provider_instance = None


def get_storage_provider() -> BaseStorageProvider:
    """
    Instantiate and return configured StorageProvider based on STORAGE_PROVIDER in .env.
    Defaults to LocalStorageProvider if unspecified or invalid.
    """
    global _provider_instance
    provider_type = os.getenv("STORAGE_PROVIDER", "local").lower().strip()

    if _provider_instance is None:
        if provider_type == "s3":
            log.info("Initializing S3StorageProvider (AWS S3 / Cloudflare R2)")
            _provider_instance = S3StorageProvider()
        elif provider_type == "neon":
            log.info("Initializing NeonStorageProvider (PostgreSQL BYTEA)")
            _provider_instance = NeonStorageProvider()
        else:
            log.info("Initializing LocalStorageProvider (Local Disk)")
            _provider_instance = LocalStorageProvider()

    return _provider_instance
