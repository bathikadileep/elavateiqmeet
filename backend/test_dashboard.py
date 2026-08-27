"""
Dashboard API test script — tests /api/v1/dashboard/overview endpoint.
"""
import unittest
import json
from backend.app import create_app
from backend.extensions import db

class DashboardTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_dashboard_overview(self):
        # Register and login user
        self.client.post("/api/v1/auth/register", json={
            "username": "dashuser",
            "email": "dash@example.com",
            "password": "password123",
            "display_name": "Dashboard Tester"
        })
        login_res = self.client.post("/api/v1/auth/login", json={
            "identity": "dashuser",
            "password": "password123"
        })
        self.assertEqual(login_res.status_code, 200)

        # Query dashboard overview
        res = self.client.get("/api/v1/dashboard/overview")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn("stats", data)
        self.assertIn("todays_meetings", data)
        self.assertIn("upcoming_meetings", data)
        self.assertIn("notifications", data)
        self.assertIn("recent_activity", data)

        self.assertEqual(data["stats"]["hosted_count"], 0)
        self.assertEqual(data["stats"]["joined_count"], 0)
        self.assertEqual(data["stats"]["attendance_rate"], 100)

if __name__ == "__main__":
    unittest.main(verbosity=2)
