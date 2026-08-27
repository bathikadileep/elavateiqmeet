"""
ElevateIQ Collaboration Suite — Automated Unit Test Suite
===========================================================
Tests Polls, Poll Options, Votes, Breakout Rooms, Breakout Assignments,
Whiteboard state snapshots, and REST API endpoints.
"""

import unittest
import time
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, Poll, PollOption, PollVote, BreakoutRoom, BreakoutAssignment, WhiteboardSnapshot


class CollaborationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                username="collabuser",
                email="collab@example.com",
                display_name="Collab User"
            )
            self.user.set_password("Password123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        # Login and obtain access token
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "collabuser",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.room_code = f"collab-{int(time.time())}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_poll_creation_voting_and_publishing(self):
        # 1. Create Poll
        res = self.client.post("/api/polls", json={
            "meeting_code": self.room_code,
            "question": "What is our primary Q3 focus?",
            "options": ["Performance", "New Features", "Bug Fixes"],
            "is_multiselect": False
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        poll_data = res.get_json()
        poll_id = poll_data["id"]
        options = poll_data["options"]
        self.assertEqual(len(options), 3)

        # 2. Vote on option
        opt_id = options[0]["id"]
        res_vote = self.client.post(f"/api/polls/{poll_id}/vote", json={
            "option_ids": [opt_id]
        }, headers=self.headers)
        self.assertEqual(res_vote.status_code, 200)
        vote_data = res_vote.get_json()
        self.assertEqual(vote_data["total_votes"], 1)

        # 3. Publish Poll
        res_pub = self.client.post(f"/api/polls/{poll_id}/publish", json={}, headers=self.headers)
        self.assertEqual(res_pub.status_code, 200)
        self.assertTrue(res_pub.get_json()["is_published"])

        # 4. List Polls for meeting
        res_list = self.client.get(f"/api/polls/meeting/{self.room_code}", headers=self.headers)
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.get_json()), 1)

    def test_breakout_rooms_lifecycle(self):
        # 1. Create Breakout Rooms
        res = self.client.post("/api/breakout/create", json={
            "meeting_code": self.room_code,
            "num_rooms": 3,
            "duration_minutes": 20,
            "auto_assign": False
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        rooms = res.get_json()
        self.assertEqual(len(rooms), 3)
        room_id = rooms[0]["id"]

        # 2. Assign user to breakout room
        res_assign = self.client.post("/api/breakout/assign", json={
            "room_id": room_id,
            "user_id": self.user_id
        }, headers=self.headers)
        self.assertEqual(res_assign.status_code, 200)

        # 3. Get active rooms
        res_get = self.client.get(f"/api/breakout/meeting/{self.room_code}", headers=self.headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(len(res_get.get_json()), 3)

        # 4. Close breakout rooms
        res_close = self.client.post("/api/breakout/close", json={
            "meeting_code": self.room_code
        }, headers=self.headers)
        self.assertEqual(res_close.status_code, 200)

    def test_whiteboard_snapshot_model(self):
        with self.app.app_context():
            snapshot = WhiteboardSnapshot(
                meeting_code=self.room_code,
                snapshot_json=[{"type": "line", "points": [10, 10, 50, 50], "color": "#ffffff"}]
            )
            db.session.add(snapshot)
            db.session.commit()

            saved = WhiteboardSnapshot.query.filter_by(meeting_code=self.room_code).first()
            self.assertIsNotNone(saved)
            self.assertEqual(len(saved.snapshot_json), 1)


if __name__ == "__main__":
    unittest.main()
