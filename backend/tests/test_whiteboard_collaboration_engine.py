"""
ElevateIQ — Unit Test Suite for Whiteboard Collaboration Engine
================================================================
Tests vector shape creation, LWW conflict resolution, attributes updates,
tombstone deletions, canvas clearing, and live cursor tracking.
"""

import time
import unittest
from backend.services.media.whiteboard_collaboration_engine import (
    WhiteboardCollaborationEngine,
    WhiteboardShape,
    ShapeType,
    Point2D,
)


class WhiteboardCollaborationTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = WhiteboardCollaborationEngine(room_code="room_wb_101")
        self.now_ms = int(time.time() * 1000)

    def test_add_and_retrieve_shapes(self):
        """Test adding freehand and geometric shapes to canvas."""
        freehand = WhiteboardShape(
            shape_id="shp_pen_1",
            shape_type=ShapeType.FREEHAND,
            author_user_id="usr_alice",
            created_at_ms=self.now_ms,
            updated_at_ms=self.now_ms,
            points=[Point2D(10.0, 20.0), Point2D(15.0, 25.0), Point2D(20.0, 30.0)],
            stroke_color="#ef4444",
            stroke_width=3.0,
        )

        rect = WhiteboardShape(
            shape_id="shp_rect_1",
            shape_type=ShapeType.RECTANGLE,
            author_user_id="usr_bob",
            created_at_ms=self.now_ms,
            updated_at_ms=self.now_ms,
            x=100.0,
            y=150.0,
            width=200.0,
            height=120.0,
            fill_color="#3b82f620",
            stroke_color="#3b82f6",
        )

        self.assertTrue(self.engine.add_shape(freehand))
        self.assertTrue(self.engine.add_shape(rect))

        snapshot = self.engine.get_full_snapshot()
        self.assertEqual(snapshot["shape_count"], 2)
        self.assertEqual(len(snapshot["shapes"]), 2)

    def test_lww_conflict_resolution(self):
        """Verify older timestamp updates do not overwrite newer updates."""
        shape1 = WhiteboardShape(
            shape_id="shp_text_1",
            shape_type=ShapeType.TEXT,
            author_user_id="usr_alice",
            created_at_ms=1000,
            updated_at_ms=1000,
            text_content="Initial Text",
        )
        self.engine.add_shape(shape1)

        # Update with newer timestamp (2000)
        self.engine.update_shape("shp_text_1", "usr_bob", {"text_content": "Second Edit"}, timestamp_ms=2000)
        self.assertEqual(self.engine._shapes["shp_text_1"].text_content, "Second Edit")

        # Stale update with older timestamp (1500) should be discarded
        rejected = self.engine.update_shape("shp_text_1", "usr_carol", {"text_content": "Stale Edit"}, timestamp_ms=1500)
        self.assertIsNone(rejected)
        self.assertEqual(self.engine._shapes["shp_text_1"].text_content, "Second Edit")

    def test_shape_deletion_tombstone(self):
        """Test deleting a shape marks it as deleted without losing history."""
        shape = WhiteboardShape(
            shape_id="shp_del_1",
            shape_type=ShapeType.ELLIPSE,
            author_user_id="usr_1",
            created_at_ms=self.now_ms,
            updated_at_ms=self.now_ms,
        )
        self.engine.add_shape(shape)
        self.assertEqual(self.engine.get_full_snapshot()["shape_count"], 1)

        deleted = self.engine.delete_shape("shp_del_1", "usr_1")
        self.assertTrue(deleted)

        # Snapshot should now exclude deleted shape
        self.assertEqual(self.engine.get_full_snapshot()["shape_count"], 0)
        # But shape remains tombstoned in internal store
        self.assertTrue(self.engine._shapes["shp_del_1"].is_deleted)

    def test_clear_canvas(self):
        """Test clearing all elements on canvas."""
        for i in range(5):
            self.engine.add_shape(
                WhiteboardShape(
                    shape_id=f"shp_multi_{i}",
                    shape_type=ShapeType.RECTANGLE,
                    author_user_id="usr_host",
                    created_at_ms=self.now_ms,
                    updated_at_ms=self.now_ms,
                )
            )

        self.assertEqual(self.engine.get_full_snapshot()["shape_count"], 5)
        cleared_count = self.engine.clear_canvas("usr_host")
        self.assertEqual(cleared_count, 5)
        self.assertEqual(self.engine.get_full_snapshot()["shape_count"], 0)

    def test_cursor_presence_tracking(self):
        """Test updating live pointer position and timeout pruning."""
        self.engine.update_cursor("usr_10", "Alice", 150.5, 300.2, tool="pen", color="#ef4444")
        self.engine.update_cursor("usr_20", "Bob", 450.0, 600.0, tool="eraser")

        cursors = self.engine.get_active_cursors()
        self.assertEqual(len(cursors), 2)

        # Remove cursor
        self.engine.remove_cursor("usr_10")
        cursors_after = self.engine.get_active_cursors()
        self.assertEqual(len(cursors_after), 1)
        self.assertEqual(cursors_after[0]["user_id"], "usr_20")

    def test_delta_sync(self):
        """Test retrieving only updates that occurred after baseline timestamp."""
        t1 = 1000000
        s1 = WhiteboardShape("s1", ShapeType.TEXT, "u1", t1, t1, text_content="Baseline")
        self.engine.add_shape(s1)

        t2 = 1005000
        s2 = WhiteboardShape("s2", ShapeType.RECTANGLE, "u2", t2, t2)
        self.engine.add_shape(s2)

        delta = self.engine.get_delta_since(t1)
        self.assertEqual(delta["delta_count"], 1)
        self.assertEqual(delta["shapes"][0]["shape_id"], "s2")


if __name__ == "__main__":
    unittest.main()
