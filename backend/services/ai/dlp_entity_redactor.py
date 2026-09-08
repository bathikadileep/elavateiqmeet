"""
Enterprise Meeting Transcription Entity Redactor & DLP Masker
=============================================================
Provides real-time Data Loss Prevention (DLP) and Personally Identifiable
Information (PII) redaction for meeting transcripts, closed captions, and chat logs.

Features:
- Payment Card Detection with Luhn (Mod 10) Checksum Validation.
- Government ID Identification (US SSN, UK NINO, Indian Aadhaar Verhoeff Check).
- Cloud Secrets & Token Detection (AWS Keys, GitHub PATs, JWTs, Private Key PEMs).
- Healthcare Identifiers (MRN, HIPAA patient IDs).
- Multiple Redaction Modes: Tokenize (HMAC pseudonym), Mask (partial), or Category Label.
- Comprehensive DLP Audit Log generation with risk scoring.
"""

from __future__ import annotations

import enum
import hashlib
import hmac
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple

logger = logging.getLogger("elevateiq.services.ai.dlp")


class EntityType(str, enum.Enum):
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    AADHAAR = "AADHAAR"
    UK_NINO = "UK_NINO"
    EMAIL = "EMAIL"
    PHONE_NUMBER = "PHONE_NUMBER"
    IP_ADDRESS = "IP_ADDRESS"
    AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
    GITHUB_TOKEN = "GITHUB_TOKEN"
    JWT_TOKEN = "JWT_TOKEN"
    PRIVATE_KEY = "PRIVATE_KEY"
    MEDICAL_RECORD_NUM = "MEDICAL_RECORD_NUM"


class RedactionStrategy(str, enum.Enum):
    LABEL = "LABEL"          # e.g. [REDACTED:CREDIT_CARD]
    MASK = "MASK"            # e.g. ************1234
    TOKENIZE = "TOKENIZE"    # e.g. [TOKEN:CC_9a4f]


@dataclass
class DetectedEntity:
    """Represents a discovered sensitive data entity in text."""
    entity_type: EntityType
    start: int
    end: int
    matched_text: str
    redacted_text: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DlpScanResult:
    """Output of DLP scan across a text transcript segment."""
    original_text: str
    redacted_text: str
    entities: List[DetectedEntity]
    risk_score: float  # 0.0 (Clean) to 1.0 (Critical)
    has_violations: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "redacted_text": self.redacted_text,
            "violations_count": len(self.entities),
            "risk_score": self.risk_score,
            "has_violations": self.has_violations,
            "entity_types": list(set(e.entity_type.value for e in self.entities)),
        }


class LuhnValidator:
    """Validates Payment Card checksums using Luhn Mod 10 algorithm."""

    @staticmethod
    def is_valid(number_str: str) -> bool:
        digits = [int(d) for d in number_str if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False

        checksum = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = d * 2
                checksum += (doubled - 9) if doubled > 9 else doubled
            else:
                checksum += d

        return checksum % 10 == 0


class VerhoeffValidator:
    """Validates 12-digit Indian Aadhaar numbers using Verhoeff Dihedral D5 check."""

    # Multiplication table
    D = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]

    # Permutation table
    P = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
    ]

    @classmethod
    def is_valid(cls, num_str: str) -> bool:
        clean = "".join(d for d in num_str if d.isdigit())
        if len(clean) != 12:
            return False

        c = 0
        reversed_digits = [int(x) for x in reversed(clean)]
        for i, digit in enumerate(reversed_digits):
            c = cls.D[c][cls.P[i % 8][digit]]
        return c == 0


class DlpEntityRedactor:
    """
    High-throughput DLP redactor for text transcripts and messages.
    """

    # Compiled high-precision regex patterns
    PATTERNS: Dict[EntityType, Pattern] = {
        # Credit Card: 13-19 digits, optional dashes or spaces
        EntityType.CREDIT_CARD: re.compile(
            r'\b(?:\d[ -]*?){13,19}\b'
        ),
        # US SSN: XXX-XX-XXXX or 9 consecutive digits
        EntityType.SSN: re.compile(
            r'\b(?!000|666|9\d\d)(\d{3})[- ]?(?!00)(\d{2})[- ]?(?!0000)(\d{4})\b'
        ),
        # Indian Aadhaar: 12 digits (XXXX XXXX XXXX or XXXXXXXXXXXX)
        EntityType.AADHAAR: re.compile(
            r'\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b'
        ),
        # UK NINO: Two letters, 6 digits, one letter A-D
        EntityType.UK_NINO: re.compile(
            r'\b[A-CEGHJ-PR-TW-Z]{2}[ -]?\d{2}[ -]?\d{2}[ -]?\d{2}[ -]?[A-D]\b',
            re.IGNORECASE
        ),
        # Standard Email
        EntityType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        ),
        # Phone: E.164 or US format
        EntityType.PHONE_NUMBER: re.compile(
            r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b'
        ),
        # IPv4
        EntityType.IP_ADDRESS: re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ),
        # AWS Access Key ID: AKIA or ASIA followed by 16 alphanumeric characters
        EntityType.AWS_ACCESS_KEY: re.compile(
            r'\b(AKIA|ASIA)[0-9A-Z]{16}\b'
        ),
        # GitHub Personal Access Token
        EntityType.GITHUB_TOKEN: re.compile(
            r'\bgh[pousr]_[A-Za-z0-9_]{36,255}\b'
        ),
        # JWT Token: three base64 segments
        EntityType.JWT_TOKEN: re.compile(
            r'\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b'
        ),
        # Private Key Header
        EntityType.PRIVATE_KEY: re.compile(
            r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
            re.IGNORECASE
        ),
        # Medical Record Number: MRN-XXXXXXX or 7-9 digit medical ID
        EntityType.MEDICAL_RECORD_NUM: re.compile(
            r'\b(?:MRN|PATIENT-ID)[-:# ]+([A-Z0-9]{6,12})\b',
            re.IGNORECASE
        ),
    }

    # Weight assigned to each entity type for risk scoring
    RISK_WEIGHTS: Dict[EntityType, float] = {
        EntityType.PRIVATE_KEY: 1.0,
        EntityType.AWS_ACCESS_KEY: 0.95,
        EntityType.GITHUB_TOKEN: 0.95,
        EntityType.CREDIT_CARD: 0.9,
        EntityType.SSN: 0.85,
        EntityType.JWT_TOKEN: 0.8,
        EntityType.AADHAAR: 0.75,
        EntityType.MEDICAL_RECORD_NUM: 0.75,
        EntityType.UK_NINO: 0.7,
        EntityType.EMAIL: 0.3,
        EntityType.PHONE_NUMBER: 0.3,
        EntityType.IP_ADDRESS: 0.2,
    }

    def __init__(self, hmac_key: str = "elevateiq-dlp-pseudonym-salt") -> None:
        self.hmac_key = hmac_key.encode("utf-8")

    def scan_and_redact(
        self,
        text: str,
        strategy: RedactionStrategy = RedactionStrategy.LABEL,
        enabled_types: Optional[Set[EntityType]] = None
    ) -> DlpScanResult:
        """
        Scans input string, applies validation algorithms, redacts sensitive matches,
        and computes risk score.
        """
        if not text:
            return DlpScanResult(original_text="", redacted_text="", entities=[], risk_score=0.0)

        active_types = enabled_types or set(EntityType)
        detected_entities: List[DetectedEntity] = []

        # Scan each pattern
        for e_type in active_types:
            pattern = self.PATTERNS.get(e_type)
            if not pattern:
                continue

            for match in pattern.finditer(text):
                matched_str = match.group(0)
                start, end = match.span()

                # Secondary algorithmic validators
                if e_type == EntityType.CREDIT_CARD:
                    clean_digits = re.sub(r'\D', '', matched_str)
                    if not LuhnValidator.is_valid(clean_digits):
                        continue  # False positive number rejected

                elif e_type == EntityType.AADHAAR:
                    clean_digits = re.sub(r'\D', '', matched_str)
                    if not VerhoeffValidator.is_valid(clean_digits):
                        continue

                # Generate replacement based on strategy
                redacted_str = self._format_redaction(matched_str, e_type, strategy)
                detected_entities.append(
                    DetectedEntity(
                        entity_type=e_type,
                        start=start,
                        end=end,
                        matched_text=matched_str,
                        redacted_text=redacted_str,
                        confidence=0.98 if e_type in (EntityType.CREDIT_CARD, EntityType.AWS_ACCESS_KEY) else 0.85,
                    )
                )

        # Sort entities by start position and resolve overlapping matches
        detected_entities.sort(key=lambda e: (e.start, -(e.end - e.start)))
        non_overlapping = self._resolve_overlaps(detected_entities)

        # Build redacted text string
        redacted_parts: List[str] = []
        last_idx = 0
        for entity in non_overlapping:
            redacted_parts.append(text[last_idx:entity.start])
            redacted_parts.append(entity.redacted_text)
            last_idx = entity.end
        redacted_parts.append(text[last_idx:])

        final_redacted_text = "".join(redacted_parts)

        # Compute aggregate risk score
        risk_score = 0.0
        if non_overlapping:
            max_weight = max(self.RISK_WEIGHTS.get(e.entity_type, 0.1) for e in non_overlapping)
            count_factor = min(1.0, 0.1 * len(non_overlapping))
            risk_score = min(1.0, round(max_weight * 0.8 + count_factor * 0.2, 2))

        return DlpScanResult(
            original_text=text,
            redacted_text=final_redacted_text,
            entities=non_overlapping,
            risk_score=risk_score,
            has_violations=len(non_overlapping) > 0,
        )

    def _format_redaction(self, raw: str, e_type: EntityType, strategy: RedactionStrategy) -> str:
        if strategy == RedactionStrategy.LABEL:
            return f"[CONFIDENTIAL_{e_type.value}]"

        elif strategy == RedactionStrategy.MASK:
            if e_type == EntityType.CREDIT_CARD:
                digits = re.sub(r'\D', '', raw)
                last4 = digits[-4:] if len(digits) >= 4 else digits
                return f"****-****-****-{last4}"
            elif e_type == EntityType.SSN:
                digits = re.sub(r'\D', '', raw)
                last4 = digits[-4:] if len(digits) >= 4 else digits
                return f"***-**-{last4}"
            elif e_type == EntityType.EMAIL:
                parts = raw.split("@")
                if len(parts) == 2 and len(parts[0]) > 2:
                    return f"{parts[0][:2]}***@{parts[1]}"
                return "***@***.com"
            else:
                return "*" * len(raw)

        elif strategy == RedactionStrategy.TOKENIZE:
            token_hash = hmac.new(self.hmac_key, raw.encode("utf-8"), hashlib.sha256).hexdigest()[:8]
            return f"[TOKEN:{e_type.value}:{token_hash}]"

        return "[REDACTED]"

    def _resolve_overlaps(self, entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Filters out nested or overlapping entity matches, favoring higher priority/longer spans."""
        if not entities:
            return []

        resolved: List[DetectedEntity] = []
        current = entities[0]

        for nxt in entities[1:]:
            if nxt.start < current.end:
                curr_len = current.end - current.start
                nxt_len = nxt.end - nxt.start
                curr_weight = self.RISK_WEIGHTS.get(current.entity_type, 0.0)
                nxt_weight = self.RISK_WEIGHTS.get(nxt.entity_type, 0.0)
                if nxt_len > curr_len or (nxt_len == curr_len and nxt_weight > curr_weight):
                    current = nxt
            else:
                resolved.append(current)
                current = nxt

        resolved.append(current)
        return resolved
