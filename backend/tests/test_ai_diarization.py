"""
ElevateIQ — Unit Test Suite for Speaker Diarization Service
============================================================
Tests transcript line speaker talk-time calculation, turn frequency, and interjection detection.
"""

import unittest
from backend.services.ai.diarization_service import DiarizationService


class AIDiarizationTestSuite(unittest.TestCase):

    def test_calculate_speaker_talktime(self):
        """Test calculating relative talk-time percentage and word count."""
        lines = [
            {"speaker_name": "Alice", "transcript_text": "Hello team, welcome to the sprint review meeting."},
            {"speaker_name": "Bob", "transcript_text": "Thanks Alice. The frontend features are complete."},
            {"speaker_name": "Alice", "transcript_text": "Great work Bob! Let us review the backend API benchmarks."}
        ]

        res = DiarizationService.calculate_speaker_talktime(lines)
        self.assertEqual(res["total_turns"], 3)
        self.assertGreater(res["total_word_count"], 15)
        self.assertEqual(len(res["speakers"]), 2)
        self.assertEqual(res["speakers"][0]["speaker_name"], "Alice")

    def test_detect_interjections(self):
        """Test identifying speaker interjections in rapid dialogue."""
        lines = [
            {"speaker_name": "Alice", "transcript_text": "We need to discuss the timeline for..."},
            {"speaker_name": "Bob", "transcript_text": "Actually, hold on, I have an urgent update regarding deployment."}
        ]

        interjections = DiarizationService.detect_interjections_and_overlaps(lines)
        self.assertEqual(len(interjections), 1)
        self.assertEqual(interjections[0]["interjector"], "Bob")


if __name__ == "__main__":
    unittest.main()
