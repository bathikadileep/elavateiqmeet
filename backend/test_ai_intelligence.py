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

    def test_whitespace_and_empty_transcript_rejection(self):
        # 1. Blank string
        res_empty = self.client.post("/api/summaries/transcript", json={
            "meeting_code": self.room_code,
            "speaker_name": "Alice",
            "transcript_text": ""
        }, headers=self.headers)
        self.assertEqual(res_empty.status_code, 400)

        # 2. Whitespace-only string
        res_whitespace = self.client.post("/api/summaries/transcript", json={
            "meeting_code": self.room_code,
            "speaker_name": "Alice",
            "transcript_text": "   \n\t   "
        }, headers=self.headers)
        self.assertEqual(res_whitespace.status_code, 400)

        # 3. Missing meeting_code
        res_no_code = self.client.post("/api/summaries/transcript", json={
            "meeting_code": "   ",
            "speaker_name": "Alice",
            "transcript_text": "Valid text"
        }, headers=self.headers)
        self.assertEqual(res_no_code.status_code, 400)

    def test_json_markdown_code_fence_cleaning(self):
        # 1. Markdown with ```json
        raw_markdown = """```json
        {
            "executive_summary": "Sprint planning completed.",
            "key_decisions": ["Deploy SFU"],
            "action_items": [{"task_description": "Load test", "assigned_to": "Bob", "due_date": "Friday"}],
            "sentiment_score": "positive",
            "sentiment_value": "0.92"
        }
        ```"""
        parsed = AISummarizerService._clean_json_response(raw_markdown)
        self.assertEqual(parsed["executive_summary"], "Sprint planning completed.")
        self.assertEqual(len(parsed["key_decisions"]), 1)

        # 2. Markdown with plain ```
        raw_plain = """```
        {
            "executive_summary": "Architecture review.",
            "key_decisions": ["Approved"],
            "action_items": [],
            "sentiment_score": "neutral",
            "sentiment_value": "0.60"
        }
        ```"""
        parsed2 = AISummarizerService._clean_json_response(raw_plain)
        self.assertEqual(parsed2["executive_summary"], "Architecture review.")

    def test_consecutive_transcript_deduplication(self):
        # Send first line
        res1 = self.client.post("/api/summaries/transcript", json={
            "meeting_code": self.room_code,
            "speaker_name": "Alice",
            "transcript_text": "Checking microphone audio levels."
        }, headers=self.headers)
        self.assertEqual(res1.status_code, 201)

        # Send identical duplicate line immediately
        res2 = self.client.post("/api/summaries/transcript", json={
            "meeting_code": self.room_code,
            "speaker_name": "Alice",
            "transcript_text": "Checking microphone audio levels."
        }, headers=self.headers)
        self.assertEqual(res2.status_code, 200)

        # Assert only 1 record persisted in DB
        res_get = self.client.get(f"/api/summaries/transcript/{self.room_code}", headers=self.headers)
        lines = res_get.get_json()
        self.assertEqual(len(lines), 1)

    def test_idempotent_summary_regeneration(self):
        # Seed transcript lines
        with self.app.app_context():
            l1 = MeetingTranscriptLine(
                meeting_code=self.room_code,
                speaker_name="Alice",
                transcript_text="We approved the sprint milestones."
            )
            db.session.add(l1)
            db.session.commit()

        # Call generate twice
        res1 = self.client.post("/api/summaries/generate", json={"meeting_code": self.room_code}, headers=self.headers)
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/summaries/generate", json={"meeting_code": self.room_code}, headers=self.headers)
        self.assertEqual(res2.status_code, 201)

        # Verify only 1 MeetingSummary exists in database
        with self.app.app_context():
            summaries = MeetingSummary.query.filter_by(meeting_code=self.room_code).all()
            self.assertEqual(len(summaries), 1)


if __name__ == "__main__":
    unittest.main()

