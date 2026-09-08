"""
ElevateIQ — Webinar Live Q&A & Stage Promotion Integration Test Suite
======================================================================
Tests attendee hand-raising, presenter stage promotion, Q&A upvoting, and moderator answers.
"""

import unittest
from backend.services.webinar_service import WebinarService


class WebinarLiveQAFlowTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = WebinarService()

    def test_stage_promotion_and_hand_raise(self):
        """Test attendee raising hand and host promoting attendee to stage."""
        res_hand = self.service.raise_hand("web_e2e_1", "att_1", "Attendee One")
        self.assertEqual(res_hand["queue_length"], 1)

        res_promo = self.service.promote_to_stage("web_e2e_1", "att_1")
        self.assertEqual(res_promo["status"], "promoted")

    def test_qa_thread_moderation(self):
        """Test asking question, upvoting, and host approval with answer."""
        q1 = self.service.ask_question("web_e2e_1", "att_2", "Attendee Two", "What is the release date?")
        q2 = self.service.ask_question("web_e2e_1", "att_3", "Attendee Three", "Is API open?")

        self.service.upvote_question("web_e2e_1", q1["id"])
        self.service.upvote_question("web_e2e_1", q1["id"])

        answered = self.service.approve_question("web_e2e_1", q1["id"], answer_text="v2 launches Q4.")
        self.assertEqual(answered["upvotes"], 2)
        self.assertEqual(answered["answer_text"], "v2 launches Q4.")


if __name__ == "__main__":
    unittest.main()
