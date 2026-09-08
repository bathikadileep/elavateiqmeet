"""
ElevateIQ — Unit Tests for Caption Punctuation Restorer & Diarization
======================================================================
Tests sentence capitalization, question mark inference, comma insertion,
profanity masking, acoustic energy speaker diarization, and transcript export.
"""

import unittest
from backend.services.ai.caption_punctuation_restorer import (
    CaptionPunctuationRestorer,
    CaptionSegment
)


class TestCaptionPunctuationRestorer(unittest.TestCase):

    def setUp(self):
        self.restorer = CaptionPunctuationRestorer(filter_profanity=True)

    def test_restore_punctuation_standard_statement(self):
        raw = "we have completed the migration of the database"
        res = self.restorer.restore_punctuation_and_case(raw)
        self.assertEqual(res, "We have completed the migration of the database.")

    def test_restore_punctuation_question_starter(self):
        raw = "can everyone see my screen"
        res = self.restorer.restore_punctuation_and_case(raw)
        self.assertEqual(res, "Can everyone see my screen?")

        raw_why = "why did the deployment fail"
        res_why = self.restorer.restore_punctuation_and_case(raw_why)
        self.assertEqual(res_why, "Why did the deployment fail?")

    def test_capitalize_single_letter_i(self):
        raw = "i think i am ready to present"
        res = self.restorer.restore_punctuation_and_case(raw)
        self.assertEqual(res, "I think I am ready to present.")

    def test_introductory_comma_insertion(self):
        raw = "hello team we are starting now"
        res = self.restorer.restore_punctuation_and_case(raw)
        self.assertEqual(res, "Hello, team we are starting now.")

    def test_profanity_redaction(self):
        raw = "what the hell is this damn bug"
        res = self.restorer.restore_punctuation_and_case(raw)
        # hell -> h***, damn -> d***
        self.assertIn("h***", res)
        self.assertIn("d***", res)
        self.assertNotIn("hell", res)
        self.assertNotIn("damn", res)

    def test_align_diarization_energy_matching(self):
        profiles = {
            "usr_alice": ("Alice Smith", 0.12),
            "usr_bob": ("Bob Jones", 0.85),
            "usr_carol": ("Carol White", 0.05)
        }

        seg = self.restorer.align_diarization(
            raw_text="i agree with the architectural direction",
            start_time_sec=12.5,
            end_time_sec=15.0,
            speaker_energy_profiles=profiles
        )

        self.assertEqual(seg.user_id, "usr_bob")
        self.assertEqual(seg.speaker_name, "Bob Jones")
        self.assertEqual(seg.formatted_text, "I agree with the architectural direction.")
        self.assertEqual(len(self.restorer.history_segments), 1)

    def test_get_transcript_summary(self):
        profiles_alice = {"u1": ("Alice", 0.9)}
        profiles_bob = {"u2": ("Bob", 0.9)}

        self.restorer.align_diarization("can you hear me", 0.0, 2.0, profiles_alice)
        self.restorer.align_diarization("yes i can hear you clearly", 2.5, 5.0, profiles_bob)

        summary = self.restorer.get_transcript_summary()
        self.assertEqual(summary["total_segments"], 2)
        self.assertIn("[00:00] Alice: Can you hear me?", summary["formatted_transcript"])
        self.assertIn("[00:02] Bob: Yes I can hear you clearly.", summary["formatted_transcript"])


if __name__ == "__main__":
    unittest.main()
