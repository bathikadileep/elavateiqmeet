"""
ElevateIQ — Unit & Integration Test Suite for Webinar Q&A & Upvoting Widget
=============================================================================
Tests submitting webinar attendee questions, upvote counts, host answering, and pinning.
"""

import unittest
from backend.services.webinar_service import WebinarService


class WebinarQATestSuite(unittest.TestCase):

    def setUp(self):
        self.service = WebinarService()

    def test_submit_question_and_upvoting(self):
        """Test submitting attendee question and upvote incrementing."""
        q = self.service.ask_question(
            room_code="web_101",
            participant_id="att_45",
            participant_name="Frank Wright",
            question="Will slides and session recordings be shared afterwards?"
        )

        self.assertEqual(q["upvotes"], 0)
        self.assertFalse(q["is_answered"])

        upvoted = self.service.upvote_question("web_101", q["id"])
        self.assertEqual(upvoted["upvotes"], 1)

    def test_host_answer_question(self):
        """Test host marking question as answered with live response."""
        q = self.service.ask_question("web_101", "att_1", "User 1", "When is v2 releasing?")
        answered = self.service.approve_question("web_101", q["id"], answer_text="v2 releases next Monday.")

        self.assertTrue(answered["is_answered"])
        self.assertEqual(answered["answer_text"], "v2 releases next Monday.")


if __name__ == "__main__":
    unittest.main()
