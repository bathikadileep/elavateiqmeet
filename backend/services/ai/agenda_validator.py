"""
ElevateIQ — AI Meeting Agenda Tracking & Time Validation Engine
================================================================
Tracks meeting topic coverage against pre-scheduled meeting agenda items,
estimating time drift per topic and alerting hosts to overrun risks.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.ai.agenda")


class AgendaValidatorService:
    """Meeting Agenda & Topic Coverage Engine."""

    @staticmethod
    def validate_agenda_coverage(agenda_topics: List[str], transcript_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Match transcript keywords against pre-planned agenda items."""
        if not agenda_topics:
            return {"covered_topics": [], "coverage_percentage": 100.0, "status": "no_agenda"}

        full_text = " ".join([t.get("transcript_text", "").lower() for t in transcript_lines])

        covered = []
        uncovered = []

        for topic in agenda_topics:
            keywords = topic.lower().split()
            if any(k in full_text for k in keywords if len(k) > 3):
                covered.append(topic)
            else:
                uncovered.append(topic)

        percentage = round((len(covered) / max(len(agenda_topics), 1)) * 100.0, 1)

        return {
            "total_agenda_topics": len(agenda_topics),
            "covered_topics": covered,
            "uncovered_topics": uncovered,
            "coverage_percentage": percentage,
            "status": "complete" if percentage >= 80.0 else "in_progress",
        }
