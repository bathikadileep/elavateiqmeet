"""
ElevateIQ — Unit Test Suite for Live Subtitle Translation & Speaker Diarization Integration
=============================================================================================
Tests combining speaker identification with neural subtitle translation streams.
"""

import unittest
from backend.services.live_caption_service import LiveCaptionService
from backend.services.ai.translation_pipeline import TranslationPipelineEngine


class LiveCaptionTranslationTestSuite(unittest.TestCase):

    def setUp(self):
        self.caption_service = LiveCaptionService()
        self.translation_engine = TranslationPipelineEngine()

    def test_caption_translation_pipeline(self):
        """Test processing speech chunk into live caption and translating to target language."""
        frame = self.caption_service.ingest_speech_chunk(
            meeting_code="room-tr-101",
            speaker_id="spk_alice",
            speaker_name="Alice",
            text="Hello team, welcome to the architecture meeting.",
            language="en-US",
            is_final=True
        )

        translated = self.translation_engine.translate_text(frame["text"], source_lang="en", target_lang="es")
        self.assertEqual(translated["target_lang"], "es")
        self.assertIn("Hola", translated["translated_text"])


if __name__ == "__main__":
    unittest.main()
