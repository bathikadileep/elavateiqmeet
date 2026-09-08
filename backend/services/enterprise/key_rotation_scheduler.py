"""
ElevateIQ — Cryptographic Key Rotation Cron Scheduler
=====================================================
Schedules automated 90-day cryptographic key rotations for JWT signing and database encryption keys.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

log = logging.getLogger("elevateiq.services.enterprise.key_scheduler")


class KeyRotationScheduler:
    """Cron Key Rotation Task Scheduler."""

    def evaluate_rotation_schedule(self, last_rotation_iso: str, interval_days: int = 90) -> bool:
        """Evaluate if cryptographic key is due for automatic rotation."""
        try:
            last_dt = datetime.fromisoformat(last_rotation_iso)
            days_passed = (datetime.now(timezone.utc) - last_dt).days
            return days_passed >= interval_days
        except Exception:
            return True
