"""
ElevateIQ — Unit Test Suite for Webinar Q&A & Breakout Orchestrator
====================================================================
Tests webinar stage promotion, Q&A upvoting, hand raise priority queues,
and round-robin breakout room allocations.
"""

import unittest
from backend.services.webinar_service import WebinarService
from backend.services.breakout_service import BreakoutService
from backend.services.telemetry_service import TelemetryService


class WebinarTestSuite(unittest.TestCase):

    def setUp(self):
        self.webinar_service = WebinarService()

    def test_qa_question_submission_and_upvoting(self):
        """Test submitting Q&A question and upvoting."""
        q = self.webinar_service.ask_question("test-room-101", "u1", "Alex", "What is the Q3 roadmap?")
        self.assertEqual(q["question"], "What is the Q3 roadmap?")
        self.assertEqual(q["upvotes"], 0)

        updated_q = self.webinar_service.upvote_question("test-room-101", q["id"])
        self.assertIsNotNone(updated_q)
        self.assertEqual(updated_q["upvotes"], 1)

    def test_hand_raise_priority_queue(self):
        """Test attendee hand-raise queueing."""
        res1 = self.webinar_service.raise_hand("test-room-101", "u1", "Alex")
        res2 = self.webinar_service.raise_hand("test-room-101", "u2", "Sarah")
        self.assertEqual(res2["queue_length"], 2)

    def test_breakout_room_creation(self):
        """Test dynamic round-robin breakout room allocation."""
        participants = ["user_1", "user_2", "user_3", "user_4", "user_5"]
        result = BreakoutService.create_breakout_rooms("main-room-code", participants, num_rooms=2, duration_minutes=20)

        self.assertEqual(result["main_room_code"], "main-room-code")
        self.assertEqual(len(result["breakout_rooms"]), 2)
        total_allocated = sum(len(r["participants"]) for r in result["breakout_rooms"])
        self.assertEqual(total_allocated, 5)

    def test_telemetry_qoe_evaluation(self):
        """Test WebRTC MOS score and QoE rating evaluation."""
        eval_excellent = TelemetryService.evaluate_qoe_score(rtt_ms=30.0, packet_loss_pct=0.1, jitter_ms=2.0)
        self.assertGreaterEqual(eval_excellent["mos_score"], 4.0)
        self.assertEqual(eval_excellent["quality_rating"], "excellent")

        eval_poor = TelemetryService.evaluate_qoe_score(rtt_ms=450.0, packet_loss_pct=8.0, jitter_ms=85.0)
        self.assertLessEqual(eval_poor["mos_score"], 2.8)


if __name__ == "__main__":
    unittest.main()
