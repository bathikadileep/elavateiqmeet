"""
ElevateIQ — NLP Action Item & Task Classifier Engine
=====================================================
Extracts actionable tasks, assignee names, and target due dates from meeting transcript lines.
"""

import re
import logging
from typing import Dict, Any, List

log = logging.getLogger("elevateiq.services.ai.action_items")


class ActionItemClassifierEngine:
    """NLP Action Item Classifier Engine."""

    ACTION_TRIGGERS = ["will do", "action item", "take note", "assigning", "deliverable", "due by", "follow up on"]

    def extract_action_items(self, transcript_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan transcript lines for assigned tasks and deliverables."""
        items = []
        for line in transcript_lines:
            text = line.get("transcript_text", "")
            speaker = line.get("speaker_name", "Unassigned")

            if any(trig in text.lower() for trig in self.ACTION_TRIGGERS):
                items.append({
                    "task_description": text,
                    "assigned_to": speaker,
                    "due_date": "Next Sprint",
                    "is_completed": False,
                })

        return items
