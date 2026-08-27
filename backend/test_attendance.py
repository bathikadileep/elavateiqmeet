"""
ElevateIQ — Attendance Tracking Unit Tests
============================================
Tests attendance endpoints:
  1. Attendance summary
  2. Meeting attendance report
  3. User attendance logs
  4. Record attendance log
"""

import unittest
import json
from backend.app import create_app
from backend.extensions import db

class AttendanceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

        # Register & Login User
        self.client.post("/api/v1/auth/register", json={
            "username": "attuser",
            "email": "att@example.com",
            "password": "password123"
        })
        self.client.post("/api/v1/auth/login", json={
            "identity": "attuser",
            "password": "password123"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_attendance_summary(self):
        res = self.client.get("/api/v1/attendance/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("attendance_percentage", data)
        self.assertIn("total_hours", data)

    def test_record_log_and_fetch_report(self):
        # Create meeting
        m_res = self.client.post("/api/v1/meetings", json={"title": "Analytics Meeting"})
        m_id = m_res.get_json()["meeting"]["id"]

        # Log Join Event
        join_res = self.client.post("/api/v1/attendance/log", json={
            "meeting_id": m_id,
            "event": "joined"
        })
        self.assertEqual(join_res.status_code, 201)

        # Log Leave Event with 1800 sec (30 min) duration
        leave_res = self.client.post("/api/v1/attendance/log", json={
            "meeting_id": m_id,
            "event": "left",
            "duration_seconds": 1800
        })
        self.assertEqual(leave_res.status_code, 201)

        # Fetch Meeting Attendance Report
        report_res = self.client.get(f"/api/v1/attendance/meetings/{m_id}")
        self.assertEqual(report_res.status_code, 200)
        report = report_res.get_json()
        self.assertEqual(report["total_participants"], 1)
        self.assertEqual(report["roster"][0]["duration_minutes"], 30.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
