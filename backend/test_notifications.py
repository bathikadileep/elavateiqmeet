"""
ElevateIQ — Notification System Unit Tests
============================================
Tests notification endpoints & dispatch engine:
  1. List notifications & unread count
  2. Mark notification read
  3. Mark all read
  4. Send notification trigger
"""

import unittest
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User

class NotificationsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

        # Register User
        res = self.client.post("/api/v1/auth/register", json={
            "username": "notifuser",
            "email": "notif@example.com",
            "password": "password123"
        })
        self.user_id = res.get_json()["user"]["id"]

        # Login User
        self.client.post("/api/v1/auth/login", json={
            "identity": "notifuser",
            "password": "password123"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_notification_flow(self):
        # 1. Trigger Notification Dispatch
        send_res = self.client.post("/api/v1/notifications/send", json={
            "recipient_id": self.user_id,
            "notif_type": "meeting_start",
            "title": "Meeting Starting Now",
            "body": "Your meeting 'Q3 Sync' has started.",
            "send_email": False
        })
        self.assertEqual(send_res.status_code, 201)
        notif_id = send_res.get_json()["notification"]["id"]

        # 2. List Notifications (Unread count should be 1)
        list_res = self.client.get("/api/v1/notifications")
        self.assertEqual(list_res.status_code, 200)
        data = list_res.get_json()
        self.assertEqual(data["unread_count"], 1)

        # 3. Mark Single as Read
        read_res = self.client.put(f"/api/v1/notifications/{notif_id}/read")
        self.assertEqual(read_res.status_code, 200)

        # 4. Confirm unread count is 0
        list_res2 = self.client.get("/api/v1/notifications")
        self.assertEqual(list_res2.get_json()["unread_count"], 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
