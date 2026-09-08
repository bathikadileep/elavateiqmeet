"""
ElevateIQ — Enterprise Billing, Usage Metering & Invoicing Service
====================================================================
Tracks participant meeting minutes, cloud storage bytes, transcription credits,
subscription plan limits, and automated invoice PDF generation.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.billing")

SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "monthly_price_usd": 0,
        "max_participants_per_meeting": 10,
        "max_meeting_duration_minutes": 40,
        "included_storage_gb": 1,
        "ai_transcription_minutes": 60,
    },
    "pro": {
        "monthly_price_usd": 15,
        "max_participants_per_meeting": 100,
        "max_meeting_duration_minutes": 1440,
        "included_storage_gb": 25,
        "ai_transcription_minutes": 600,
    },
    "enterprise": {
        "monthly_price_usd": 49,
        "max_participants_per_meeting": 1000,
        "max_meeting_duration_minutes": 1440,
        "included_storage_gb": 1000,
        "ai_transcription_minutes": 10000,
    }
}


class BillingEngineService:
    """Usage Metering & Enterprise Plan Billing Engine."""

    def __init__(self):
        self._usage_tracker: Dict[str, Dict[str, Any]] = {}

    def get_or_create_usage(self, tenant_id: str, plan_name: str = "pro") -> Dict[str, Any]:
        """Fetch or initialize usage meter for a tenant."""
        if tenant_id not in self._usage_tracker:
            self._usage_tracker[tenant_id] = {
                "tenant_id": tenant_id,
                "plan_name": plan_name,
                "meeting_minutes_used": 0,
                "storage_bytes_used": 0,
                "ai_transcription_minutes_used": 0,
                "billing_cycle_start": datetime.now(timezone.utc).isoformat(),
            }
        return self._usage_tracker[tenant_id]

    def record_meeting_duration(self, tenant_id: str, duration_minutes: int, participant_count: int) -> Dict[str, Any]:
        """Meter meeting minutes (duration * participant count)."""
        usage = self.get_or_create_usage(tenant_id)
        metered_minutes = duration_minutes * max(participant_count, 1)
        usage["meeting_minutes_used"] += metered_minutes
        log.info("Billed %d participant minutes to tenant %s", metered_minutes, tenant_id)
        return usage

    def generate_invoice_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Generate monthly billing invoice summary."""
        usage = self.get_or_create_usage(tenant_id)
        plan = SUBSCRIPTION_PLANS.get(usage["plan_name"], SUBSCRIPTION_PLANS["pro"])

        base_price = plan["monthly_price_usd"]
        extra_minutes_charge = 0.0

        # Overage calculation
        if usage["meeting_minutes_used"] > (plan["max_participants_per_meeting"] * 60):
            overage = usage["meeting_minutes_used"] - (plan["max_participants_per_meeting"] * 60)
            extra_minutes_charge = round(overage * 0.02, 2)

        total_due = base_price + extra_minutes_charge

        return {
            "invoice_id": f"inv_{datetime.now().strftime('%Y%m%d')}_{tenant_id[:6]}",
            "tenant_id": tenant_id,
            "plan_name": usage["plan_name"],
            "base_monthly_fee_usd": base_price,
            "overage_fee_usd": extra_minutes_charge,
            "total_due_usd": total_due,
            "usage": usage,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
