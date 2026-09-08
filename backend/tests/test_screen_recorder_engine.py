"""
ElevateIQ — Unit Test Suite for Screen Recorder Engine
======================================================
Tests session initialization, state transitions (pause, resume, stop),
bookmarking, rolling segment generation, and legal hold locking.
"""

import time
import unittest
from backend.services.media.screen_recorder_engine import (
    ScreenRecorderEngine,
    RecordingState,
    VideoResolution,
)


class ScreenRecorderEngineTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = ScreenRecorderEngine(base_storage_dir="/tmp/elviq_test_recs")
        self.session = self.engine.start_recording(
            room_code="room_test_101",
            host_user_id="usr_host_1",
            resolution=VideoResolution.FULL_HD_1080P,
            fps=30,
            bitrate_kbps=4000,
        )

    def test_start_recording_creates_active_session(self):
        """Verify recording session starts in RECORDING state."""
        self.assertIsNotNone(self.session.recording_id)
        self.assertEqual(self.session.state, RecordingState.RECORDING)
        self.assertEqual(self.session.resolution, VideoResolution.FULL_HD_1080P)
        self.assertEqual(self.session.fps, 30)
        self.assertEqual(self.session.bitrate_kbps, 4000)

    def test_prevent_duplicate_active_recording_per_room(self):
        """Verify calling start on the same room returns existing active session."""
        dup_session = self.engine.start_recording(
            room_code="room_test_101",
            host_user_id="usr_other_host",
        )
        self.assertEqual(dup_session.recording_id, self.session.recording_id)

    def test_pause_and_resume_flow(self):
        """Verify pause/resume state transitions and paused duration calculation."""
        rec_id = self.session.recording_id

        # Pause
        self.assertTrue(self.engine.pause_recording(rec_id))
        self.assertEqual(self.session.state, RecordingState.PAUSED)
        self.assertIsNotNone(self.session.pause_time_ms)

        # Pause again should be False (already paused)
        self.assertFalse(self.engine.pause_recording(rec_id))

        time.sleep(0.05)  # 50ms pause

        # Resume
        self.assertTrue(self.engine.resume_recording(rec_id))
        self.assertEqual(self.session.state, RecordingState.RECORDING)
        self.assertGreaterEqual(self.session.total_paused_duration_ms, 40)
        self.assertIsNone(self.session.pause_time_ms)

    def test_add_bookmark(self):
        """Verify adding chapter bookmarks."""
        rec_id = self.session.recording_id
        bm = self.engine.add_bookmark(rec_id, "Sprint Demo Intro", "usr_host_1")

        self.assertIsNotNone(bm)
        self.assertEqual(bm.label, "Sprint Demo Intro")
        self.assertEqual(len(self.session.bookmarks), 1)

    def test_seal_segment_and_checksum(self):
        """Verify rolling segment chunk creation and SHA-256 calculation."""
        rec_id = self.session.recording_id
        seg = self.engine.seal_segment(rec_id, approx_duration_ms=60000)

        self.assertIsNotNone(seg)
        self.assertEqual(seg.segment_index, 1)
        self.assertGreater(seg.file_size_bytes, 0)
        self.assertEqual(len(seg.sha256_checksum), 64)
        self.assertEqual(len(self.session.segments), 1)

    def test_stop_recording_finalizes_session(self):
        """Verify stopping session seals final chunk and marks STOPPED."""
        rec_id = self.session.recording_id
        stopped = self.engine.stop_recording(rec_id)

        self.assertIsNotNone(stopped)
        self.assertEqual(stopped.state, RecordingState.STOPPED)
        self.assertIsNotNone(stopped.end_time_ms)
        self.assertGreaterEqual(stopped.total_duration_ms, 0)
        self.assertGreaterEqual(len(stopped.segments), 1)

    def test_legal_hold_toggle(self):
        """Verify setting and unsetting compliance legal hold."""
        rec_id = self.session.recording_id
        self.assertFalse(self.session.legal_hold_enabled)

        self.assertTrue(self.engine.set_legal_hold(rec_id, True))
        self.assertTrue(self.session.legal_hold_enabled)

        self.assertTrue(self.engine.set_legal_hold(rec_id, False))
        self.assertFalse(self.session.legal_hold_enabled)

    def test_list_room_recordings(self):
        """Verify room recording query serialization."""
        recs = self.engine.list_room_recordings("room_test_101")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["recording_id"], self.session.recording_id)
        self.assertEqual(recs[0]["resolution"], VideoResolution.FULL_HD_1080P.value)


if __name__ == "__main__":
    unittest.main()
