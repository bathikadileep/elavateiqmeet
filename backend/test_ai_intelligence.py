"""
ElevateIQ AI Intelligence Suite — Automated Unit Test Suite
============================================================
Tests transcript logging, AI meeting summary generation, key decision extraction,
action items parsing, sentiment analysis, and REST API endpoints.
"""

import unittest
import time
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, MeetingTranscriptLine, MeetingSummary, ActionItem
from backend.services.ai_summarizer import AISummarizerService


class AIIntelligenceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                username="aiuser",
                email="ai@example.com",
                display_name="AI Analyst"
            )
            self.user.set_password("Password123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        # Login and obtain access token
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "aiuser",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.room_code = f"ai-{int(time.time())}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_transcript_logging_and_retrieval(self):
        # 1. Add transcript line
        res = self.client.post("/api/summaries/transcript", json={
            "meeting_code": self.room_code,
            "speaker_name": "Alice",
            "transcript_text": "We agreed to deploy the new SFU media engine by Friday."
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)

        # 2. Add second transcript line
        res2 = self.client.post("/api/summaries/transcript", json={
            "meeting_code": self.room_code,
            "speaker_name": "Bob",
            "transcript_text": "I will do the load testing task for 100 participants."
        }, headers=self.headers)
        self.assertEqual(res2.status_code, 201)

        # 3. Retrieve full transcript
        res_get = self.client.get(f"/api/summaries/transcript/{self.room_code}", headers=self.headers)
        self.assertEqual(res_get.status_code, 200)
        lines = res_get.get_json()
        self.assertEqual(len(lines), 2)

    def test_ai_summary_generation_pipeline(self):
        # Seed transcript lines
        with self.app.app_context():
            l1 = MeetingTranscriptLine(
                meeting_code=self.room_code,
                speaker_name="Alice",
                transcript_text="We approved the Q3 roadmap and budget."
            )
            l2 = MeetingTranscriptLine(
                meeting_code=self.room_code,
                speaker_name="Bob",
                transcript_text="I will do the database migration task."
            )
            db.session.add_all([l1, l2])
            db.session.commit()

        # Trigger AI Summary generation
        res_gen = self.client.post("/api/summaries/generate", json={
            "meeting_code": self.room_code
        }, headers=self.headers)
        self.assertEqual(res_gen.status_code, 201)
        summary = res_gen.get_json()

        self.assertIn("executive_summary", summary)
        self.assertTrue(len(summary["key_decisions"]) > 0)
        self.assertTrue(len(summary["action_items"]) > 0)

        # Retrieve stored summary
        res_get = self.client.get(f"/api/summaries/meeting/{self.room_code}", headers=self.headers)
        self.assertEqual(res_get.status_code, 200)

    def test_fallback_nlp_summarizer_service(self):
        sample_transcript = [
            {"speaker_name": "Carol", "transcript_text": "We decided to launch the vector whiteboard feature."},
            {"speaker_name": "Dave", "transcript_text": "I will action item the security audit."}
        ]
        result = AISummarizerService.generate_meeting_summary(sample_transcript)
        self.assertIn("executive_summary", result)
        self.assertEqual(len(result["key_decisions"]), 1)
        self.assertEqual(len(result["action_items"]), 1)
        self.assertEqual(result["action_items"][0]["assigned_to"], "Dave")


if __name__ == "__main__":
    unittest.main()
