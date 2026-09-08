"""
ElevateIQ — Unit Test Suite for Live Captioning & WebVTT Generator
===================================================================
Tests speech chunk ingestion, speaker identification, subtitle history buffers, and WebVTT export.
"""

import unittest
from backend.services.live_caption_service import LiveCaptionService


class LiveCaptionTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = LiveCaptionService()

    def test_caption_ingestion_and_buffering(self):
        """Test ingesting speech transcript chunks and retrieving history."""
        frame = self.service.ingest_speech_chunk(
            meeting_code="room-cap-101",
            speaker_id="spk_1",
            speaker_name="Alice Smith",
            text="Welcome to the quarterly product demo.",
            language="en-US",
            is_final=True
        )

        self.assertEqual(frame["speaker_name"], "Alice Smith")
        self.assertEqual(frame["text"], "Welcome to the quarterly product demo.")

        recent = self.service.get_recent_captions("room-cap-101", limit=5)
        self.assertEqual(len(recent), 1)

    def test_webvtt_export_generation(self):
        """Test generating WebVTT subtitle track string."""
        self.service.ingest_speech_chunk("room-cap-vtt", "spk_1", "Bob", "Hello everyone.", is_final=True)
        self.service.ingest_speech_chunk("room-cap-vtt", "spk_2", "Carol", "Hi Bob!", is_final=True)

        vtt = self.service.export_webvtt("room-cap-vtt")
        self.assertTrue(vtt.startswith("WEBVTT"))
        self.assertIn("Bob", vtt)
        self.assertIn("Carol", vtt)


if __name__ == "__main__":
    unittest.main()
