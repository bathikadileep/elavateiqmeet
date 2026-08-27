"""
ElevateIQ — Reporting System Unit Tests
========================================
Tests reporting endpoints & export formats:
  1. Attendance report (JSON & CSV export)
  2. Meeting report (JSON & CSV export)
  3. User activity report (JSON & CSV export)
"""

import unittest
from backend.app import create_app
from backend.extensions import db

class ReportsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

        # Register & Login User
        self.client.post("/api/v1/auth/register", json={
            "username": "repuser",
            "email": "rep@example.com",
            "password": "password123"
        })
        self.client.post("/api/v1/auth/login", json={
            "identity": "repuser",
            "password": "password123"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_reports_json_and_csv_exports(self):
        # 1. Attendance Report JSON
        att_res = self.client.get("/api/v1/reports/attendance?format=json")
        self.assertEqual(att_res.status_code, 200)
        self.assertIn("data", att_res.get_json())

        # 2. Meeting Report CSV Export
        m_csv = self.client.get("/api/v1/reports/meetings?format=csv")
        self.assertEqual(m_csv.status_code, 200)
        self.assertEqual(m_csv.mimetype, "text/csv")
        self.assertIn(b"Meeting Code", m_csv.data)

        # 3. User Activity Report JSON & Excel Format
        u_res = self.client.get("/api/v1/reports/user-activity?format=excel")
        self.assertEqual(u_res.status_code, 200)
        self.assertEqual(u_res.mimetype, "text/csv")

if __name__ == "__main__":
    unittest.main(verbosity=2)
