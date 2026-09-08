"""
ElevateIQ — Virtual Webinar & Large-Scale Event Service
========================================================
Manages presenter/audience stage promotion, green room isolation, live Q&A moderation queues,
upvoting, and attendee hand-raise priority queues.
"""

import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.webinar")


class WebinarService:
    """Large-Scale Webinar Event Manager."""

    def __init__(self):
        self._qa_threads: Dict[str, List[Dict[str, Any]]] = {}
        self._hand_raises: Dict[str, List[Dict[str, Any]]] = {}
        self._stage_presenters: Dict[str, List[str]] = {}

    def ask_question(self, room_code: str, participant_id: str, participant_name: str, question: str) -> Dict[str, Any]:
        """Submit a Q&A question for moderator review."""
        if room_code not in self._qa_threads:
            self._qa_threads[room_code] = []

        q_item = {
            "id": str(uuid.uuid4())[:8],
            "room_code": room_code,
            "participant_id": participant_id,
            "participant_name": participant_name,
            "question": (question or "").strip(),
            "upvotes": 0,
            "is_approved": False,
            "is_answered": False,
            "answer_text": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._qa_threads[room_code].append(q_item)
        log.info("Q&A Question submitted in room %s by %s", room_code, participant_name)
        return q_item

    def upvote_question(self, room_code: str, question_id: str) -> Optional[Dict[str, Any]]:
        """Upvote a Q&A question to increase moderator visibility."""
        threads = self._qa_threads.get(room_code, [])
        for q in threads:
            if q["id"] == question_id:
                q["upvotes"] += 1
                return q
        return None

    def approve_question(self, room_code: str, question_id: str, answer_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Approve and answer a question for public webinar display."""
        threads = self._qa_threads.get(room_code, [])
        for q in threads:
            if q["id"] == question_id:
                q["is_approved"] = True
                if answer_text:
                    q["is_answered"] = True
                    q["answer_text"] = answer_text
                return q
        return None

    def raise_hand(self, room_code: str, participant_id: str, participant_name: str) -> Dict[str, Any]:
        """Add participant to hand-raise priority queue."""
        if room_code not in self._hand_raises:
            self._hand_raises[room_code] = []

        hand_item = {
            "participant_id": participant_id,
            "participant_name": participant_name,
            "raised_at": datetime.now(timezone.utc).isoformat(),
        }

        # Avoid duplicates
        if not any(h["participant_id"] == participant_id for h in self._hand_raises[room_code]):
            self._hand_raises[room_code].append(hand_item)

        return {"room_code": room_code, "queue_length": len(self._hand_raises[room_code]), "item": hand_item}

    def promote_to_stage(self, room_code: str, participant_id: str) -> Dict[str, Any]:
        """Promote attendee from audience to stage presenter role."""
        if room_code not in self._stage_presenters:
            self._stage_presenters[room_code] = []

        if participant_id not in self._stage_presenters[room_code]:
            self._stage_presenters[room_code].append(participant_id)

        # Lower hand if raised
        if room_code in self._hand_raises:
            self._hand_raises[room_code] = [
                h for h in self._hand_raises[room_code] if h["participant_id"] != participant_id
            ]

        return {"status": "promoted", "participant_id": participant_id, "room_code": room_code}


_GLOBAL_WEBINAR_SERVICE = WebinarService()

def get_webinar_service() -> WebinarService:
    return _GLOBAL_WEBINAR_SERVICE
