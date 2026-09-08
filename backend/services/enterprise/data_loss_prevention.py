"""
ElevateIQ — Data Loss Prevention (DLP) Real-Time Scanner Engine
================================================================
Scans chat messages, transcript streams, and uploaded documents for sensitive PII/PHI
(SSN, Credit Cards, API Keys, AWS Secrets, Passwords) and applies automatic redacting or blocking.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

log = logging.getLogger("elevateiq.services.enterprise.dlp")


class DataLossPreventionEngine:
    """Enterprise Real-Time Data Loss Prevention (DLP) Scanner."""

    PATTERNS = {
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
        "AWS_API_KEY": r"\bAKIA[0-9A-Z]{16}\b",
        "GENERIC_SECRET": r"(?i)\b(?:secret|password|bearer|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{8,})['\"]?",
    }

    def __init__(self):
        self._compiled_patterns = {k: re.compile(v) for k, v in self.PATTERNS.items()}
        self._offense_log: List[Dict[str, Any]] = []

    def scan_text_content(self, text: str, source_context: str = "chat", user_id: str = "anon") -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Scan input text for sensitive DLP policy violations.
        Returns: (is_blocked, redacted_text, offenses_detected)
        """
        if not text:
            return False, text, []

        offenses = []
        redacted_text = text

        for policy_name, regex in self._compiled_patterns.items():
            matches = regex.findall(text)
            if matches:
                for m in matches:
                    snippet = m if isinstance(m, str) else m[0]
                    offenses.append({
                        "policy_name": policy_name,
                        "matched_snippet": snippet[:10] + "...",
                        "source": source_context,
                        "user_id": user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    # Mask snippet with asterisks
                    redacted_text = redacted_text.replace(snippet, "[REDACTED_DLP_VIOLATION]")

        is_blocked = len(offenses) > 0
        if is_blocked:
            self._offense_log.extend(offenses)
            log.warning("DLP Violation detected in context '%s' by user %s (Policies: %s)",
                        source_context, user_id, [o["policy_name"] for o in offenses])

        return is_blocked, redacted_text, offenses

    def get_offense_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent DLP violation history logs."""
        return self._offense_log[-limit:]
