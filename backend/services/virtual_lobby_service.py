"""
ElevateIQ — Virtual Waiting Room & Pre-Screening Lobby Engine
=============================================================
Manages host admit/deny waiting room queues, guest pre-screening checks,
passcode verification, and real-time lobby notifications.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.virtual_lobby")


class VirtualLobbyService:
    """Enterprise Virtual Waiting Room & Guest Pre-Screening Engine."""

    def __init__(self):
        self._lobbies: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def join_lobby_queue(self, meeting_code: str, user_id: str, display_name: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Place a guest participant into the virtual lobby queue pending host approval.
        """
        if meeting_code not in self._lobbies:
            self._lobbies[meeting_code] = {}

        now_iso = datetime.now(timezone.utc).isoformat()
        entry = {
            "user_id": user_id,
            "display_name": display_name,
            "email": email,
            "meeting_code": meeting_code,
            "status": "WAITING",
            "joined_lobby_at": now_iso,
            "decision_at": None,
            "decided_by": None,
        }

        self._lobbies[meeting_code][user_id] = entry
        log.info("User '%s' (%s) entered waiting room lobby for meeting %s", display_name, user_id, meeting_code)
        return entry

    def evaluate_guest_passcode(self, meeting_code: str, user_id: str, provided_passcode: str, expected_passcode_hash: str) -> bool:
        """Verify pre-entry passcode before placing in queue."""
        from backend.extensions import bcrypt
        return bcrypt.check_password_hash(expected_passcode_hash, provided_passcode)

    def process_host_decision(self, meeting_code: str, user_id: str, host_id: str, action: str) -> Optional[Dict[str, Any]]:
        """
        Host action: 'ADMIT', 'DENY', or 'ADMIT_ALL'.
        """
        room_lobby = self._lobbies.get(meeting_code)
        if not room_lobby:
            return None

        if action == "ADMIT_ALL":
            now_iso = datetime.now(timezone.utc).isoformat()
            admitted_list = []
            for uid, entry in room_lobby.items():
                if entry["status"] == "WAITING":
                    entry["status"] = "ADMITTED"
                    entry["decision_at"] = now_iso
                    entry["decided_by"] = host_id
                    admitted_list.append(entry)
            log.info("Host %s admitted ALL guests (%d) in room %s", host_id, len(admitted_list), meeting_code)
            return {"action": "ADMIT_ALL", "admitted_count": len(admitted_list)}

        entry = room_lobby.get(user_id)
        if not entry:
            return None

        status_map = {"ADMIT": "ADMITTED", "DENY": "DENIED"}
        entry["status"] = status_map.get(action, "WAITING")
        entry["decision_at"] = datetime.now(timezone.utc).isoformat()
        entry["decided_by"] = host_id

        log.info("Host %s %s user %s in room %s", host_id, action, user_id, meeting_code)
        return entry

    def get_waiting_guests(self, meeting_code: str) -> List[Dict[str, Any]]:
        """Retrieve list of currently waiting guests in room lobby."""
        room_lobby = self._lobbies.get(meeting_code, {})
        return [entry for entry in room_lobby.values() if entry["status"] == "WAITING"]
