"""
ElevateIQ — Dynamic Breakout Rooms Orchestrator
===============================================
Handles automatic or manual participant splitting into sub-breakout rooms,
timer synchronization, broadcast announcements, and automatic main room return.
"""

import math
import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.breakout")


class BreakoutService:
    """Breakout Room Allocation & Lifecycle Manager."""

    @staticmethod
    def create_breakout_rooms(main_room_code: str, participant_ids: List[str], num_rooms: int = 2, duration_minutes: int = 15) -> Dict[str, Any]:
        """
        Split participants into designated breakout sub-rooms using balanced round-robin allocation.
        """
        if num_rooms < 1:
            num_rooms = 2

        shuffled = list(participant_ids)
        random.shuffle(shuffled)

        rooms: List[Dict[str, Any]] = []
        for i in range(num_rooms):
            sub_code = f"{main_room_code}-b{i+1}"
            rooms.append({
                "sub_room_code": sub_code,
                "room_name": f"Breakout Room {i+1}",
                "participants": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        for index, p_id in enumerate(shuffled):
            room_index = index % num_rooms
            rooms[room_index]["participants"].append(p_id)

        log.info("Created %d breakout rooms for main room %s (%d participants)", num_rooms, main_room_code, len(participant_ids))

        return {
            "main_room_code": main_room_code,
            "num_rooms": num_rooms,
            "duration_minutes": duration_minutes,
            "breakout_rooms": rooms,
        }

    @staticmethod
    def broadcast_announcement(main_room_code: str, message: str) -> Dict[str, Any]:
        """Broadcast host message across all active breakout rooms."""
        cleaned_msg = (message or "").strip()
        log.info("Broadcasting to breakout rooms of %s: %s", main_room_code, cleaned_msg)
        return {
            "main_room_code": main_room_code,
            "broadcast_message": cleaned_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
