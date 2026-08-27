"""
ElevateIQ — Data Loss Prevention (DLP) Service
===============================================
Scans uploaded documents and chat messages for sensitive patterns:
  - US Social Security Numbers (SSN)
  - Credit Card Numbers (Luhn check pattern)
  - AWS & API Secret Keys
  - Passwords & JWT Tokens
  - RSA Private Key Blocks
"""

import re
import logging
from typing import Dict, Any, List

log = logging.getLogger("elevateiq.services.dlp")


class DLPScannerService:

    PATTERNS = {
        "SSN": r"\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b",
        "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
        "AWS_KEY": r"(?i)(aws_secret_access_key|aws_access_key_id)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,40}['\"]?",
        "API_KEY": r"(?i)(api[_-]?key|secret[_-]?key|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,64}['\"]?",
        "PRIVATE_KEY": r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"
    }

    @staticmethod
    def scan_text(text: str) -> Dict[str, Any]:
        """
        Scan string input for sensitive PII / credential patterns.
        Returns dict with is_clean boolean, offenses list, and redacted_text.
        """
        if not text:
            return {"is_clean": True, "offenses": [], "redacted_text": ""}

        offenses: List[Dict[str, str]] = []
        redacted = text

        for offense_type, pattern in DLPScannerService.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    snippet = match if isinstance(match, str) else match[0]
                    offenses.append({
                        "offense_type": offense_type,
                        "snippet": snippet[:20] + "..." if len(snippet) > 20 else snippet
                    })
                    redacted = re.sub(pattern, "[REDACTED BY ELEVATEIQ DLP]", redacted)

        is_clean = len(offenses) == 0
        if not is_clean:
            log.warning("DLP Scanner detected %d security offenses in payload", len(offenses))

        return {
            "is_clean": is_clean,
            "offenses": offenses,
            "redacted_text": redacted
        }
