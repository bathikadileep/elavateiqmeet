"""
ElevateIQ — SIP / H.323 Trunking Dial-Plan & Carrier Failover Router
=====================================================================
Normalizes phone numbers to ITU-T E.164 standard, matches regex dial-plans,
manages outbound PSTN/SIP carrier failover (Twilio, Telnyx, Bandwidth),
and processes DTMF IVR state transitions for conference bridge dial-ins.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("elevateiq.services.media.sip.dialplan")


class CarrierPriority(int, Enum):
    """Outbound SIP trunk carrier routing priority."""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3


@dataclass
class SipTrunkCarrier:
    """Represents an outbound PSTN / SIP trunk provider."""
    carrier_id: str
    carrier_name: str
    gateway_fqdn: str
    priority: CarrierPriority
    is_active: bool = True
    consecutive_failures: int = 0
    max_concurrent_channels: int = 100
    active_calls: int = 0


@dataclass
class DialPlanRule:
    """Pattern matching rule for routing phone numbers to meeting bridges."""
    rule_id: str
    pattern_regex: str
    description: str
    target_bridge: str
    strip_digits: int = 0
    prepend_digits: str = ""
    require_pin: bool = True
    is_emergency: bool = False


class SipDialPlanRouter:
    """
    Enterprise SIP & PSTN Dial-Plan Routing Engine.
    Handles E.164 normalization, rule matching, carrier health failover, and DTMF IVRs.
    """

    def __init__(self):
        self.carriers: Dict[str, SipTrunkCarrier] = {}
        self.dial_plan_rules: List[DialPlanRule] = []
        self._initialize_default_carriers()
        self._initialize_default_dial_plans()

    def _initialize_default_carriers(self) -> None:
        """Register default multi-carrier SIP trunk providers for high availability."""
        self.carriers["carrier_twilio"] = SipTrunkCarrier(
            carrier_id="carrier_twilio",
            carrier_name="Twilio Super Network",
            gateway_fqdn="elevateiq-pstn.pstn.twilio.com",
            priority=CarrierPriority.PRIMARY
        )
        self.carriers["carrier_telnyx"] = SipTrunkCarrier(
            carrier_id="carrier_telnyx",
            carrier_name="Telnyx Global IP",
            gateway_fqdn="sip.telnyx.com",
            priority=CarrierPriority.SECONDARY
        )
        self.carriers["carrier_bandwidth"] = SipTrunkCarrier(
            carrier_id="carrier_bandwidth",
            carrier_name="Bandwidth Inc",
            gateway_fqdn="sbc.bandwidth.com",
            priority=CarrierPriority.TERTIARY
        )

    def _initialize_default_dial_plans(self) -> None:
        """Register default meeting dial-in patterns and emergency bypasses."""
        self.dial_plan_rules = [
            # Emergency 911 / 112 bypass
            DialPlanRule(
                rule_id="rule_e911",
                pattern_regex=r"^(911|112|999)$",
                description="Emergency Services Direct Bypass",
                target_bridge="psap_emergency_gateway",
                require_pin=False,
                is_emergency=True
            ),
            # US / Canada Toll-Free Conference Access (+1 800/888/877/866)
            DialPlanRule(
                rule_id="rule_us_tollfree",
                pattern_regex=r"^\+1(800|888|877|866|855|844|833)\d{7}$",
                description="North America Toll-Free Bridge",
                target_bridge="bridge_na_tollfree",
                require_pin=True
            ),
            # UK / Europe Access (+44, +49, +33)
            DialPlanRule(
                rule_id="rule_europe_bridge",
                pattern_regex=r"^\+(44|49|33)\d{8,12}$",
                description="Europe Unified Regional Bridge",
                target_bridge="bridge_eu_central",
                require_pin=True
            ),
            # Standard Global E.164 Catch-all
            DialPlanRule(
                rule_id="rule_global_standard",
                pattern_regex=r"^\+\d{7,15}$",
                description="Global Standard E.164 Meeting Bridge",
                target_bridge="bridge_global_sfu",
                require_pin=True
            )
        ]

    @staticmethod
    def normalize_to_e164(raw_number: str, default_country_code: str = "+1") -> str:
        """
        Clean and format raw telephone number string into ITU-T E.164 representation.
        Example: '(415) 555-0199' -> '+14155550199'.
        """
        cleaned = re.sub(r"[^\d+]", "", raw_number.strip())
        if not cleaned:
            return ""

        # Check if already leading with '+'
        if cleaned.startswith("+"):
            return cleaned

        # Handle 10-digit North American numbers
        if len(cleaned) == 10 and default_country_code == "+1":
            return f"+1{cleaned}"

        # Handle numbers starting with country code without plus
        if cleaned.startswith("1") and len(cleaned) == 11:
            return f"+{cleaned}"

        return f"{default_country_code}{cleaned}"

    def match_dial_plan(self, normalized_number: str) -> Optional[Tuple[DialPlanRule, str]]:
        """
        Evaluate dial-plan rules against a normalized E.164 phone number.
        Returns matching (DialPlanRule, transformed_number).
        """
        for rule in self.dial_plan_rules:
            if re.match(rule.pattern_regex, normalized_number):
                transformed = normalized_number
                if rule.strip_digits > 0:
                    transformed = transformed[rule.strip_digits:]
                if rule.prepend_digits:
                    transformed = rule.prepend_digits + transformed

                log.info("SipDialPlan: Matched number %s to rule '%s' -> target '%s'",
                         normalized_number, rule.description, rule.target_bridge)
                return rule, transformed

        log.warning("SipDialPlan: No matching dial-plan rule for number %s", normalized_number)
        return None

    def select_active_carrier(self) -> SipTrunkCarrier:
        """
        Select highest priority healthy carrier with available concurrent capacity.
        Falls back to secondary and tertiary carriers upon failure.
        """
        active_sorted = sorted(
            [c for c in self.carriers.values() if c.is_active and c.active_calls < c.max_concurrent_channels],
            key=lambda c: c.priority.value
        )

        if not active_sorted:
            raise ConnectionError("PSTN Gateway Exhaustion: All registered SIP trunk carriers are offline or at capacity.")

        selected = active_sorted[0]
        selected.active_calls += 1
        log.info("SipDialPlan: Allocated carrier %s (Priority %d, Active Calls: %d)",
                 selected.carrier_name, selected.priority.value, selected.active_calls)
        return selected

    def record_carrier_failure(self, carrier_id: str) -> None:
        """Mark a carrier failure; disable if consecutive failures exceed threshold."""
        if carrier_id in self.carriers:
            c = self.carriers[carrier_id]
            c.consecutive_failures += 1
            if c.active_calls > 0:
                c.active_calls -= 1

            if c.consecutive_failures >= 3:
                c.is_active = False
                log.error("SipDialPlan: Tripped circuit! Carrier %s marked INACTIVE after 3 failures.", c.carrier_name)

    def release_carrier_call(self, carrier_id: str) -> None:
        """Release a call from carrier concurrent channel tally."""
        if carrier_id in self.carriers and self.carriers[carrier_id].active_calls > 0:
            self.carriers[carrier_id].active_calls -= 1

    def process_ivr_dtmf_input(
        self,
        current_digits: str,
        new_digit: str,
        expected_pin: str
    ) -> Tuple[str, bool, bool]:
        """
        Process incoming DTMF tone keypresses during IVR bridge dial-in.
        Returns (accumulated_digits: str, is_complete: bool, is_valid: bool).
        """
        # '#' is the standard terminator digit
        if new_digit == "#":
            is_valid = (current_digits == expected_pin)
            log.info("SipDialPlan: IVR PIN submitted '%s' -> Valid: %s", current_digits, is_valid)
            return current_digits, True, is_valid

        # '*' resets the input buffer
        if new_digit == "*":
            return "", False, False

        # Accumulate numeric digit (0-9)
        if new_digit.isdigit():
            accumulated = current_digits + new_digit
            if len(accumulated) == len(expected_pin):
                is_valid = (accumulated == expected_pin)
                return accumulated, True, is_valid
            return accumulated, False, False

        return current_digits, False, False
