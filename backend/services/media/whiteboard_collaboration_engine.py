"""
ElevateIQ — Collaborative Vector Whiteboard Engine
===================================================
Real-time multi-user interactive whiteboard state synchronization engine.
Supports vector shape primitives (Bézier paths, rectangles, text, sticky notes),
Last-Write-Wins (LWW) CRDT conflict resolution, live user cursor presence,
and compact binary / delta diff serialization for WebRTC data channels.
"""

from __future__ import annotations

import copy
import enum
import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set

log = logging.getLogger("elevateiq.services.media.whiteboard")


class ShapeType(str, enum.Enum):
    FREEHAND = "freehand"          # Pen stroke points
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    STICKY_NOTE = "sticky_note"
    ERASER_MASK = "eraser_mask"


@dataclass
class Point2D:
    x: float
    y: float
    pressure: float = 1.0

    def to_dict(self) -> Dict[str, float]:
        return {"x": round(self.x, 2), "y": round(self.y, 2), "p": round(self.pressure, 2)}


@dataclass
class WhiteboardShape:
    """Vector element on the whiteboard canvas."""
    shape_id: str
    shape_type: ShapeType
    author_user_id: str
    created_at_ms: int
    updated_at_ms: int
    points: List[Point2D] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    stroke_color: str = "#000000"
    fill_color: str = "transparent"
    stroke_width: float = 2.0
    opacity: float = 1.0
    text_content: Optional[str] = None
    is_deleted: bool = False
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "shape_id": self.shape_id,
            "type": self.shape_type.value,
            "author": self.author_user_id,
            "created": self.created_at_ms,
            "updated": self.updated_at_ms,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "w": round(self.width, 2),
            "h": round(self.height, 2),
            "stroke": self.stroke_color,
            "fill": self.fill_color,
            "stroke_width": self.stroke_width,
            "opacity": self.opacity,
            "deleted": self.is_deleted,
            "version": self.version,
        }
        if self.points:
            d["points"] = [p.to_dict() for p in self.points]
        if self.text_content is not None:
            d["text"] = self.text_content
        return d


@dataclass
class UserCursorPresence:
    user_id: str
    display_name: str
    cursor_x: float
    cursor_y: float
    active_tool: str = "select"
    color: str = "#4f46e5"
    last_ping_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.display_name,
            "x": round(self.cursor_x, 2),
            "y": round(self.cursor_y, 2),
            "tool": self.active_tool,
            "color": self.color,
            "ping": self.last_ping_ms,
        }


class WhiteboardCollaborationEngine:
    """
    Manages interactive vector whiteboard state per meeting room.
    Resolves concurrent edits via Last-Write-Wins (LWW) element timestamps.
    """

    CURSOR_TIMEOUT_MS = 15000  # 15s inactive cursor expiry

    def __init__(self, room_code: str):
        self.room_code = room_code
        self._shapes: Dict[str, WhiteboardShape] = {}
        self._cursors: Dict[str, UserCursorPresence] = {}
        self._action_log: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Shape Operations
    # -------------------------------------------------------------------------

    def add_shape(self, shape: WhiteboardShape) -> bool:
        """Add a new vector shape to the whiteboard."""
        if shape.shape_id in self._shapes:
            # Check LWW conflict
            existing = self._shapes[shape.shape_id]
            if shape.updated_at_ms <= existing.updated_at_ms:
                log.debug("Rejecting older add_shape for %s", shape.shape_id)
                return False

        self._shapes[shape.shape_id] = shape
        self._action_log.append({"action": "add", "shape_id": shape.shape_id, "time": shape.updated_at_ms})
        return True

    def update_shape(
        self,
        shape_id: str,
        user_id: str,
        updates: Dict[str, Any],
        timestamp_ms: Optional[int] = None
    ) -> Optional[WhiteboardShape]:
        """Update existing shape attributes (move, resize, restyle)."""
        shape = self._shapes.get(shape_id)
        if not shape or shape.is_deleted:
            return None

        ts = timestamp_ms or int(time.time() * 1000)
        if ts < shape.updated_at_ms:
            log.warning("Out-of-order shape update discarded for %s", shape_id)
            return None

        for k, v in updates.items():
            if hasattr(shape, k) and k not in ("shape_id", "author_user_id", "created_at_ms"):
                setattr(shape, k, v)

        shape.updated_at_ms = ts
        shape.version += 1
        self._action_log.append({"action": "update", "shape_id": shape_id, "user": user_id, "time": ts})
        return shape

    def delete_shape(self, shape_id: str, user_id: str, timestamp_ms: Optional[int] = None) -> bool:
        """Tombstone a shape for collaborative deletion sync."""
        shape = self._shapes.get(shape_id)
        if not shape:
            return False

        ts = timestamp_ms or int(time.time() * 1000)
        shape.is_deleted = True
        shape.updated_at_ms = ts
        shape.version += 1
        self._action_log.append({"action": "delete", "shape_id": shape_id, "user": user_id, "time": ts})
        return True

    def clear_canvas(self, user_id: str) -> int:
        """Tombstone all non-deleted shapes on the canvas."""
        count = 0
        ts = int(time.time() * 1000)
        for shape in self._shapes.values():
            if not shape.is_deleted:
                shape.is_deleted = True
                shape.updated_at_ms = ts
                shape.version += 1
                count += 1
        self._action_log.append({"action": "clear", "user": user_id, "count": count, "time": ts})
        return count

    # -------------------------------------------------------------------------
    # Cursor Presence
    # -------------------------------------------------------------------------

    def update_cursor(
        self,
        user_id: str,
        display_name: str,
        x: float,
        y: float,
        tool: str = "pen",
        color: str = "#4f46e5"
    ) -> UserCursorPresence:
        """Update live pointer position for a participant."""
        now_ms = int(time.time() * 1000)
        cursor = UserCursorPresence(
            user_id=user_id,
            display_name=display_name,
            cursor_x=x,
            cursor_y=y,
            active_tool=tool,
            color=color,
            last_ping_ms=now_ms,
        )
        self._cursors[user_id] = cursor
        return cursor

    def remove_cursor(self, user_id: str):
        """Remove participant cursor when they leave room."""
        self._cursors.pop(user_id, None)

    def get_active_cursors(self) -> List[Dict[str, Any]]:
        """Return list of non-expired participant cursors."""
        cutoff = int(time.time() * 1000) - self.CURSOR_TIMEOUT_MS
        active = [c for c in self._cursors.values() if c.last_ping_ms >= cutoff]
        return [c.to_dict() for c in active]

    # -------------------------------------------------------------------------
    # State Snapshot & Delta Synchronization
    # -------------------------------------------------------------------------

    def get_full_snapshot(self) -> Dict[str, Any]:
        """Return full current canvas state for new participants joining the room."""
        visible_shapes = [s.to_dict() for s in self._shapes.values() if not s.is_deleted]
        return {
            "room_code": self.room_code,
            "shape_count": len(visible_shapes),
            "shapes": visible_shapes,
            "cursors": self.get_active_cursors(),
            "timestamp": int(time.time() * 1000),
        }

    def get_delta_since(self, timestamp_ms: int) -> Dict[str, Any]:
        """Return only shapes created or modified after a given timestamp."""
        modified = [
            s.to_dict() for s in self._shapes.values()
            if s.updated_at_ms > timestamp_ms
        ]
        return {
            "room_code": self.room_code,
            "delta_count": len(modified),
            "shapes": modified,
            "timestamp": int(time.time() * 1000),
        }
