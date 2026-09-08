"""
ElevateIQ — Unit Tests for AI Meeting Coach Service
====================================================
Tests speech turn recording, monologue threshold triggers, interruption tracking,
talk-time distribution, Gini-based inclusivity indexing, and executive scorecard generation.
"""

import unittest
from backend.services.ai.meeting_coach_service import MeetingCoachService, SpeakerTurn, InterruptionEvent


class TestMeetingCoachService(unittest.TestCase):

    def setUp(self):
        self.coach = MeetingCoachService(room_code="room-coach-101", monologue_threshold_sec=100.0)

    def test_register_participant(self):
        p = self.coach.register_participant("usr_alice", "Alice Johnson")
        self.assertEqual(p.user_id, "usr_alice")
        self.assertEqual(p.display_name, "Alice Johnson")
        self.assertEqual(p.total_talk_time_sec, 0.0)

        # Idempotent registration
        p2 = self.coach.register_participant("usr_alice", "Alice Johnson")
        self.assertIs(p, p2)

    def test_record_speech_turn_normal(self):
        res = self.coach.record_speech_turn(
            user_id="usr_bob",
            display_name="Bob Smith",
            duration_sec=30.0,
            word_count=75,
            sentiment=0.4,
            energy=0.8
        )
        self.assertEqual(res["user_id"], "usr_bob")
        self.assertFalse(res["is_monologue"])
        self.assertEqual(res["wpm"], 150.0)
        self.assertEqual(len(self.coach.turns), 1)

        p = self.coach.participants["usr_bob"]
        self.assertEqual(p.turn_count, 1)
        self.assertEqual(p.total_words, 75)
        self.assertEqual(p.average_sentiment, 0.4)
        self.assertEqual(p.average_energy, 0.8)

    def test_monologue_detection_alert(self):
        # Monologue threshold is 100.0s
        res = self.coach.record_speech_turn(
            user_id="usr_charlie",
            display_name="Charlie Brown",
            duration_sec=120.0,
            word_count=240
        )
        self.assertTrue(res["is_monologue"])
        p = self.coach.participants["usr_charlie"]
        self.assertEqual(p.monologue_count, 1)
        self.assertEqual(p.max_monologue_sec, 120.0)

    def test_interruption_tracking(self):
        event = self.coach.record_interruption(
            interrupter_id="usr_david",
            interrupter_name="David King",
            interruptee_id="usr_eva",
            interruptee_name="Eva Green",
            overlap_duration_sec=1.2
        )
        self.assertEqual(event.interrupter_id, "usr_david")
        self.assertEqual(event.interruptee_id, "usr_eva")
        self.assertEqual(len(self.coach.interruptions), 1)

        p_david = self.coach.participants["usr_david"]
        self.assertEqual(p_david.interruptions_initiated, 1)
        self.assertEqual(p_david.interruptions_received, 0)

        p_eva = self.coach.participants["usr_eva"]
        self.assertEqual(p_eva.interruptions_initiated, 0)
        self.assertEqual(p_eva.interruptions_received, 1)

    def test_talk_time_distribution(self):
        self.coach.record_speech_turn("u1", "Speaker 1", 60.0, 120)
        self.coach.record_speech_turn("u2", "Speaker 2", 40.0, 80)

        dist = self.coach.get_talk_time_distribution()
        self.assertEqual(dist["total_speech_time_sec"], 100.0)
        self.assertEqual(dist["participant_count"], 2)
        self.assertEqual(dist["distribution"]["u1"]["percentage"], 60.0)
        self.assertEqual(dist["distribution"]["u2"]["percentage"], 40.0)

    def test_inclusivity_index_equal_distribution(self):
        # Perfectly equal talk time: 50s each -> Inclusivity index should be 100%
        self.coach.record_speech_turn("u1", "Speaker 1", 50.0, 100)
        self.coach.record_speech_turn("u2", "Speaker 2", 50.0, 100)

        index = self.coach.compute_inclusivity_index()
        self.assertAlmostEqual(index, 100.0, delta=1.0)

    def test_inclusivity_index_heavily_skewed(self):
        # One speaker talks for 990s, another for 10s
        self.coach.record_speech_turn("u1", "Speaker 1", 990.0, 2000)
        self.coach.record_speech_turn("u2", "Speaker 2", 10.0, 20)

        index = self.coach.compute_inclusivity_index()
        # Inclusivity should be significantly lower than 100
        self.assertLess(index, 60.0)

    def test_generate_coach_scorecard(self):
        self.coach.record_speech_turn("u1", "Alice", 150.0, 300) # Monologue
        self.coach.record_speech_turn("u2", "Bob", 30.0, 50)
        self.coach.record_speech_turn("u3", "Charlie", 20.0, 30)
        self.coach.record_interruption("u1", "Alice", "u2", "Bob", 0.8)

        card = self.coach.generate_coach_scorecard()
        self.assertEqual(card["room_code"], "room-coach-101")
        self.assertIn("inclusivity_index", card)
        self.assertIn("overall_effectiveness_score", card)
        self.assertEqual(card["total_interruptions"], 1)
        self.assertEqual(card["total_turns"], 3)
        self.assertTrue(len(card["recommendations"]) > 0)


if __name__ == "__main__":
    unittest.main()
