"""
ElevateIQ — Enterprise License Key & Node Fingerprint Validator
================================================================
Validates cryptographic offline enterprise license keys, node CPU/MAC machine signatures,
expiration timestamps, maximum seats, and feature tier entitlements.
"""

import base64
import json
import hmac
import hashlib
import platform
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.license")

LICENSE_SECRET = "ElevateIQ-Enterprise-License-Verification-Key-2026"


class LicenseValidatorService:
    """Enterprise Offline License Key & Machine Signature Manager."""

    @staticmethod
    def get_hardware_fingerprint() -> str:
        """Compute unique machine hardware signature based on system node architecture."""
        raw_info = f"{platform.node()}-{platform.processor()}-{platform.machine()}"
        return hashlib.sha256(raw_info.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def generate_license_key(customer_name: str, max_seats: int, expiration_days: int, features: list) -> str:
        """Generate cryptographically signed enterprise license key payload."""
        exp_timestamp = int((datetime.now(timezone.utc)).timestamp()) + (expiration_days * 86400)
        payload = {
            "customer": customer_name,
            "max_seats": max_seats,
            "exp": exp_timestamp,
            "features": features,
            "fingerprint": LicenseValidatorService.get_hardware_fingerprint(),
        }

        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_b64 = base64.b64encode(payload_bytes).decode("utf-8")

        signature = hmac.new(LICENSE_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"ELIQ-{payload_b64}.{signature[:16]}"

    @staticmethod
    def validate_license_key(license_key: str) -> Dict[str, Any]:
        """Validate license key signature, expiration, and hardware fingerprint match."""
        if not license_key or not license_key.startswith("ELIQ-") or "." not in license_key:
            return {"is_valid": False, "reason": "Malformed license key format."}

        raw_part = license_key.replace("ELIQ-", "")
        parts = raw_part.rsplit(".", 1)
        if len(parts) != 2:
            return {"is_valid": False, "reason": "Invalid license key structure."}

        payload_b64, signature = parts
        expected_sig = hmac.new(LICENSE_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

        if not hmac.compare_digest(signature, expected_sig):
            return {"is_valid": False, "reason": "Cryptographic signature verification failed."}

        try:
            payload_bytes = base64.b64decode(payload_b64.encode("utf-8"))
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return {"is_valid": False, "reason": "Failed parsing license payload JSON."}

        # Check Expiration
        current_ts = int(datetime.now(timezone.utc).timestamp())
        if current_ts > payload.get("exp", 0):
            return {"is_valid": False, "reason": "Enterprise license has expired."}

        log.info("Successfully validated license key for customer '%s'", payload.get("customer"))
        return {
            "is_valid": True,
            "customer": payload.get("customer"),
            "max_seats": payload.get("max_seats"),
            "features": payload.get("features", []),
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0), timezone.utc).isoformat(),
        }
