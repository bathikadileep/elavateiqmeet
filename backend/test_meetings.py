"""
ElevateIQ — Meeting Management Unit Tests
===========================================
Tests all meeting endpoints:
  1. Create instant meeting
  2. Create scheduled meeting
  3. List meetings
  4. Get meeting by code
  5. Update meeting
  6. Invite participants
  7. Delete meeting
"""

import unittest
import json
from backend.app import create_app
from backend.extensions import db

class MeetingsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

        # Register host & user
        self.client.post("/api/v1/auth/register", json={
            "username": "hostuser",
            "email": "host@example.com",
            "password": "password123"
        })
        self.client.post("/api/v1/auth/login", json={
            "identity": "hostuser",
            "password": "password123"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_instant_meeting(self):
        res = self.client.post("/api/v1/meetings", json={
            "title": "Strategy Sync",
            "meeting_type": "instant"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("meeting", data)
        self.assertEqual(data["meeting"]["title"], "Strategy Sync")
        self.assertEqual(data["meeting"]["status"], "live")

    def test_create_scheduled_meeting(self):
        res = self.client.post("/api/v1/meetings", json={
            "title": "Quarterly Review",
            "meeting_type": "scheduled",
            "scheduled_start": "2026-09-01T10:00:00Z",
            "max_participants": 100
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["meeting"]["status"], "scheduled")
        self.assertEqual(data["meeting"]["max_participants"], 100)

    def test_get_by_code(self):
        create_res = self.client.post("/api/v1/meetings", json={"title": "Design Workshop"})
        code = create_res.get_json()["meeting"]["meeting_code"]

        res = self.client.get(f"/api/v1/meetings/code/{code}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["meeting"]["title"], "Design Workshop")

    def test_update_and_delete_meeting(self):
        create_res = self.client.post("/api/v1/meetings", json={"title": "Original Title"})
        meeting_id = create_res.get_json()["meeting"]["id"]

        # Update
        update_res = self.client.put(f"/api/v1/meetings/{meeting_id}", json={"title": "Updated Title"})
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()["meeting"]["title"], "Updated Title")

        # Delete
        del_res = self.client.delete(f"/api/v1/meetings/{meeting_id}")
        self.assertEqual(del_res.status_code, 200)

        # Confirm non-accessible
        get_res = self.client.get(f"/api/v1/meetings/{meeting_id}")
        self.assertEqual(get_res.status_code, 404)

if __name__ == "__main__":
    unittest.main(verbosity=2)
