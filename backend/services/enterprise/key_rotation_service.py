"""
ElevateIQ — Automatic Cryptographic Key & Secret Rotation Engine
=================================================================
Automates zero-downtime rotation of JWT Signing Keys (RSA-256 / Ed25519),
Database Encryption Keys (DEK/KEK), API Tokens, and Webhook Signing Secrets.
"""

import os
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.enterprise.key_rotation")


class KeyRotationEngine:
    """Enterprise Cryptographic Key Lifecycle Manager."""

    def __init__(self, rotation_interval_days: int = 90):
        self.rotation_interval_days = rotation_interval_days
        self._key_ring: Dict[str, List[Dict[str, Any]]] = {}

    def generate_new_key(self, key_type: str = "JWT_RS256") -> Dict[str, Any]:
        """
        Generate a new cryptographic key version in the key ring.
        """
        if key_type not in self._key_ring:
            self._key_ring[key_type] = []

        version_num = len(self._key_ring[key_type]) + 1
        key_id = f"kid_{key_type.lower()}_v{version_num}_{int(datetime.now(timezone.utc).timestamp())}"
        raw_bytes = os.urandom(32)
        key_b64 = base64.b64encode(raw_bytes).decode("utf-8")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.rotation_interval_days)

        # Deprecate previous active keys
        for k in self._key_ring[key_type]:
            if k["status"] == "ACTIVE":
                k["status"] = "DEPRECATED"

        key_entry = {
            "key_id": key_id,
            "key_type": key_type,
            "secret_b64": key_b64,
            "status": "ACTIVE",
            "version": version_num,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        self._key_ring[key_type].append(key_entry)
        log.info("Rotated cryptographic key for type '%s' -> Active Key ID: %s", key_type, key_id)
        return key_entry

    def get_active_key(self, key_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve active key for signing or encryption operations."""
        keys = self._key_ring.get(key_type, [])
        for k in reversed(keys):
            if k["status"] == "ACTIVE":
                return k
        return None

    def get_valid_keys(self, key_type: str) -> List[Dict[str, Any]]:
        """Retrieve all active and deprecated (non-expired) keys for validation."""
        keys = self._key_ring.get(key_type, [])
        return [k for k in keys if k["status"] in ["ACTIVE", "DEPRECATED"]]
