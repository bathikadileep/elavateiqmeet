"""
ElevateIQ — Comprehensive Pytest API Test Suite (Module 7)
==========================================================
100+ test cases covering every REST endpoint, input validation,
authorization, error handling, and edge-case database constraints.

Run with:
    python -m pytest backend/test_comprehensive_api.py -v
"""

import io
import json
import unittest
from datetime import datetime, timedelta, timezone
from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.models import (
    User, Meeting, MeetingParticipant, Notification,
    BreakoutRoom, BreakoutAssignment,
    Poll, PollOption, PollVote,
    MeetingTranscriptLine, MeetingSummary,
    APIKey, WebhookSubscription,
    SecurityAuditLog, IPRestrictionRule,
    MeetingRecording, File, AttendanceLog,
)


class BaseTestCase(unittest.TestCase):
    """Shared setup/teardown creating app, db, and seeding a default user."""

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                username="testuser",
                email="test@elevateiq.com",
                display_name="Test User",
                status="active",
            )
            self.user.set_password("SecurePass123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        # Login to obtain access token
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "testuser",
            "password": "SecurePass123!",
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_second_user(self):
        """Helper to create a second user and return their ID."""
        with self.app.app_context():
            user2 = User(
                username="user2",
                email="user2@elevateiq.com",
                display_name="Second User",
                status="active",
            )
            user2.set_password("Password456!")
            db.session.add(user2)
            db.session.commit()
            return user2.id


# ═══════════════════════════════════════════════════════════════════════════════
# 1. AUTHENTICATION TESTS (18 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthRegister(BaseTestCase):
    """POST /api/v1/auth/register"""

    def test_register_success(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@elevateiq.com",
            "password": "Password123!",
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn("user", res.get_json())

    def test_register_missing_fields(self):
        res = self.client.post("/api/v1/auth/register", json={"username": "x"})
        self.assertIn(res.status_code, [400, 422])

    def test_register_short_username(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "ab",
            "email": "ab@test.com",
            "password": "Password123!",
        })
        self.assertIn(res.status_code, [400, 422])

    def test_register_invalid_email(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "notanemail",
            "password": "Password123!",
        })
        self.assertIn(res.status_code, [400, 422])

    def test_register_short_password(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "email": "valid@test.com",
            "password": "12345",
        })
        self.assertIn(res.status_code, [400, 422])

    def test_register_duplicate_username(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "other@test.com",
            "password": "Password123!",
        })
        self.assertEqual(res.status_code, 409)

    def test_register_duplicate_email(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "otheruser",
            "email": "test@elevateiq.com",
            "password": "Password123!",
        })
        self.assertEqual(res.status_code, 409)

    def test_register_with_display_name(self):
        res = self.client.post("/api/v1/auth/register", json={
            "username": "dispuser",
            "email": "disp@elevateiq.com",
            "password": "Password123!",
            "display_name": "Display Name",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["user"]["display_name"], "Display Name")


class TestAuthLogin(BaseTestCase):
    """POST /api/v1/auth/login"""

    def test_login_with_username(self):
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "testuser",
            "password": "SecurePass123!",
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.get_json())

    def test_login_with_email(self):
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "test@elevateiq.com",
            "password": "SecurePass123!",
        })
        self.assertEqual(res.status_code, 200)

    def test_login_wrong_password(self):
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "testuser",
            "password": "WrongPassword!",
        })
        self.assertEqual(res.status_code, 401)

    def test_login_nonexistent_user(self):
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "ghost",
            "password": "Password123!",
        })
        self.assertEqual(res.status_code, 401)

    def test_login_missing_fields(self):
        res = self.client.post("/api/v1/auth/login", json={})
        self.assertIn(res.status_code, [400, 422])

    def test_login_suspended_user(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            user.status = "suspended"
            db.session.commit()
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "testuser",
            "password": "SecurePass123!",
        })
        self.assertEqual(res.status_code, 401)


class TestAuthEndpoints(BaseTestCase):
    """Logout, Refresh, Me, Password Flows"""

    def test_logout(self):
        res = self.client.post("/api/v1/auth/logout")
        self.assertEqual(res.status_code, 200)

    def test_me_authenticated(self):
        res = self.client.get("/api/v1/auth/me", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["user"]["username"], "testuser")

    def test_me_unauthenticated(self):
        anon_client = self.app.test_client()
        res = anon_client.get("/api/v1/auth/me")
        self.assertIn(res.status_code, [401, 422])

    def test_forgot_password(self):
        res = self.client.post("/api/v1/auth/forgot-password", json={
            "email": "test@elevateiq.com",
        })
        self.assertEqual(res.status_code, 200)

    def test_forgot_password_nonexistent_email(self):
        res = self.client.post("/api/v1/auth/forgot-password", json={
            "email": "ghost@test.com",
        })
        # Should return 200 to prevent email enumeration
        self.assertEqual(res.status_code, 200)

    def test_forgot_and_reset_password_flow(self):
        # Step 1: Forgot
        res = self.client.post("/api/v1/auth/forgot-password", json={
            "email": "test@elevateiq.com",
        })
        self.assertEqual(res.status_code, 200)
        reset_token = res.get_json().get("reset_token")
        self.assertIsNotNone(reset_token)

        # Step 2: Reset
        res2 = self.client.post("/api/v1/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewPassword789!",
        })
        self.assertEqual(res2.status_code, 200)

        # Step 3: Login with new password
        res3 = self.client.post("/api/v1/auth/login", json={
            "identity": "testuser",
            "password": "NewPassword789!",
        })
        self.assertEqual(res3.status_code, 200)

    def test_reset_password_invalid_token(self):
        res = self.client.post("/api/v1/auth/reset-password", json={
            "token": "invalid-token-xyz",
            "new_password": "SomePassword!",
        })
        self.assertIn(res.status_code, [400, 422])

    def test_change_password(self):
        res = self.client.post("/api/v1/auth/change-password", json={
            "current_password": "SecurePass123!",
            "new_password": "ChangedPass456!",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_change_password_wrong_current(self):
        res = self.client.post("/api/v1/auth/change-password", json={
            "current_password": "WrongCurrent!",
            "new_password": "NewPass123!",
        }, headers=self.headers)
        self.assertIn(res.status_code, [400, 422])

    def test_change_password_too_short(self):
        res = self.client.post("/api/v1/auth/change-password", json={
            "current_password": "SecurePass123!",
            "new_password": "12345",
        }, headers=self.headers)
        self.assertIn(res.status_code, [400, 422])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MEETING TESTS (15 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMeetings(BaseTestCase):
    """Meeting CRUD endpoints"""

    def _create_meeting(self, title="Test Meeting", meeting_type="instant"):
        return self.client.post("/api/v1/meetings", json={
            "title": title,
            "meeting_type": meeting_type,
        }, headers=self.headers)

    def test_create_instant_meeting(self):
        res = self._create_meeting()
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("meeting", data)
        self.assertIn("meeting_code", data["meeting"])

    def test_create_scheduled_meeting(self):
        start = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        res = self.client.post("/api/v1/meetings", json={
            "title": "Scheduled Meeting",
            "meeting_type": "scheduled",
            "scheduled_start": start,
            "scheduled_end": end,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)

    def test_create_meeting_invalid_type(self):
        res = self.client.post("/api/v1/meetings", json={
            "title": "Bad Type",
            "meeting_type": "invalid_type",
        }, headers=self.headers)
        self.assertIn(res.status_code, [400, 422])

    def test_create_meeting_invalid_max_participants(self):
        res = self.client.post("/api/v1/meetings", json={
            "title": "Too Many",
            "max_participants": 9999,
        }, headers=self.headers)
        self.assertIn(res.status_code, [400, 422])

    def test_list_meetings(self):
        self._create_meeting()
        res = self.client.get("/api/v1/meetings", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json()["meetings"], list)

    def test_get_meeting_by_code(self):
        create_res = self._create_meeting()
        code = create_res.get_json()["meeting"]["meeting_code"]
        res = self.client.get(f"/api/v1/meetings/code/{code}", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_get_meeting_by_invalid_code(self):
        res = self.client.get("/api/v1/meetings/code/nonexistent", headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_get_meeting_by_id(self):
        create_res = self._create_meeting()
        meeting_id = create_res.get_json()["meeting"]["id"]
        res = self.client.get(f"/api/v1/meetings/{meeting_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_update_meeting(self):
        create_res = self._create_meeting()
        meeting_id = create_res.get_json()["meeting"]["id"]
        res = self.client.put(f"/api/v1/meetings/{meeting_id}", json={
            "title": "Updated Title",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["meeting"]["title"], "Updated Title")

    def test_delete_meeting(self):
        create_res = self._create_meeting()
        meeting_id = create_res.get_json()["meeting"]["id"]
        res = self.client.delete(f"/api/v1/meetings/{meeting_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_delete_nonexistent_meeting(self):
        res = self.client.delete("/api/v1/meetings/nonexistent-id", headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_meeting_history(self):
        self._create_meeting()
        res = self.client.get("/api/v1/meetings/history", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json()["meetings"], list)

    def test_invite_participants(self):
        user2_id = self._create_second_user()
        create_res = self._create_meeting()
        meeting_id = create_res.get_json()["meeting"]["id"]
        res = self.client.post(f"/api/v1/meetings/{meeting_id}/invite", json={
            "emails": ["user2@elevateiq.com"],
            "usernames": [],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.get_json()["invited_count"], 1)

    def test_invite_to_nonexistent_meeting(self):
        res = self.client.post("/api/v1/meetings/fake-id/invite", json={
            "emails": ["user@test.com"],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_create_meeting_unauthenticated(self):
        anon_client = self.app.test_client()
        res = anon_client.post("/api/v1/meetings", json={"title": "Fail"})
        self.assertIn(res.status_code, [401, 422])


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BREAKOUT ROOM TESTS (7 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestBreakoutRooms(BaseTestCase):
    """Breakout Room CRUD endpoints"""

    def _create_meeting_and_code(self):
        res = self.client.post("/api/v1/meetings", json={
            "title": "Breakout Host Meeting",
        }, headers=self.headers)
        return res.get_json()["meeting"]["meeting_code"]

    def test_create_breakout_rooms(self):
        code = self._create_meeting_and_code()
        res = self.client.post("/api/breakout/create", json={
            "meeting_code": code,
            "num_rooms": 3,
            "duration_minutes": 10,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(res.get_json()), 3)

    def test_create_breakout_missing_code(self):
        res = self.client.post("/api/breakout/create", json={
            "num_rooms": 2,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_list_breakout_rooms(self):
        code = self._create_meeting_and_code()
        self.client.post("/api/breakout/create", json={
            "meeting_code": code,
            "num_rooms": 2,
        }, headers=self.headers)
        res = self.client.get(f"/api/breakout/meeting/{code}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), 2)

    def test_assign_participant(self):
        code = self._create_meeting_and_code()
        create_res = self.client.post("/api/breakout/create", json={
            "meeting_code": code,
            "num_rooms": 2,
            "auto_assign": False,
        }, headers=self.headers)
        rooms = create_res.get_json()
        room_id = rooms[0]["id"]
        res = self.client.post("/api/breakout/assign", json={
            "room_id": room_id,
            "user_id": self.user_id,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_assign_missing_fields(self):
        res = self.client.post("/api/breakout/assign", json={}, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_close_breakout_rooms(self):
        code = self._create_meeting_and_code()
        self.client.post("/api/breakout/create", json={
            "meeting_code": code,
            "num_rooms": 2,
        }, headers=self.headers)
        res = self.client.post("/api/breakout/close", json={
            "meeting_code": code,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)

        # Verify rooms are no longer active
        list_res = self.client.get(f"/api/breakout/meeting/{code}", headers=self.headers)
        self.assertEqual(len(list_res.get_json()), 0)

    def test_close_breakout_missing_code(self):
        res = self.client.post("/api/breakout/close", json={}, headers=self.headers)
        self.assertEqual(res.status_code, 400)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. POLLS TESTS (8 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolls(BaseTestCase):
    """Live In-Meeting Polling endpoints"""

    def _create_poll(self, meeting_code="test-poll-room"):
        return self.client.post("/api/polls", json={
            "meeting_code": meeting_code,
            "question": "What is the best framework?",
            "options": ["React", "Vue", "Angular", "Svelte"],
            "is_multiselect": False,
        }, headers=self.headers)

    def test_create_poll(self):
        res = self._create_poll()
        self.assertEqual(res.status_code, 201)
        self.assertIn("question", res.get_json())

    def test_create_poll_missing_fields(self):
        res = self.client.post("/api/polls", json={
            "meeting_code": "room",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_create_poll_insufficient_options(self):
        res = self.client.post("/api/polls", json={
            "meeting_code": "room",
            "question": "Only one?",
            "options": ["Single"],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_list_polls(self):
        self._create_poll("poll-room")
        res = self.client.get("/api/polls/meeting/poll-room", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 1)

    def test_vote_on_poll(self):
        create_res = self._create_poll()
        poll = create_res.get_json()
        poll_id = poll["id"]
        option_id = poll["options"][0]["id"]
        res = self.client.post(f"/api/polls/{poll_id}/vote", json={
            "option_ids": [option_id],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_vote_empty_options(self):
        create_res = self._create_poll()
        poll_id = create_res.get_json()["id"]
        res = self.client.post(f"/api/polls/{poll_id}/vote", json={
            "option_ids": [],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_publish_poll(self):
        create_res = self._create_poll()
        poll_id = create_res.get_json()["id"]
        res = self.client.post(f"/api/polls/{poll_id}/publish", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["is_published"])

    def test_close_poll(self):
        create_res = self._create_poll()
        poll_id = create_res.get_json()["id"]
        res = self.client.post(f"/api/polls/{poll_id}/close", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["is_closed"])


# ═══════════════════════════════════════════════════════════════════════════════
# 5. AI SUMMARIES & TRANSCRIPTS TESTS (6 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAISummaries(BaseTestCase):
    """AI Meeting Summaries & Transcripts endpoints"""

    def test_add_transcript_line(self):
        res = self.client.post("/api/summaries/transcript", json={
            "meeting_code": "sum-room",
            "speaker_name": "Test User",
            "transcript_text": "Hello everyone, let's begin the standup.",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)

    def test_add_transcript_missing_fields(self):
        res = self.client.post("/api/summaries/transcript", json={
            "meeting_code": "sum-room",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_get_transcript(self):
        self.client.post("/api/summaries/transcript", json={
            "meeting_code": "sum-room",
            "speaker_name": "Speaker A",
            "transcript_text": "First line of transcript.",
        }, headers=self.headers)
        res = self.client.get("/api/summaries/transcript/sum-room", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 1)

    def test_generate_summary(self):
        # Add some transcript lines first
        for i in range(3):
            self.client.post("/api/summaries/transcript", json={
                "meeting_code": "gen-room",
                "speaker_name": f"Speaker {i}",
                "transcript_text": f"Discussion point number {i + 1}.",
            }, headers=self.headers)

        res = self.client.post("/api/summaries/generate", json={
            "meeting_code": "gen-room",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        self.assertIn("executive_summary", res.get_json())

    def test_generate_summary_missing_code(self):
        res = self.client.post("/api/summaries/generate", json={}, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_get_summary(self):
        # Add transcript + generate summary
        self.client.post("/api/summaries/transcript", json={
            "meeting_code": "get-sum-room",
            "speaker_name": "Speaker",
            "transcript_text": "Important decision made.",
        }, headers=self.headers)
        self.client.post("/api/summaries/generate", json={
            "meeting_code": "get-sum-room",
        }, headers=self.headers)

        res = self.client.get("/api/summaries/meeting/get-sum-room", headers=self.headers)
        self.assertEqual(res.status_code, 200)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DEVELOPER PORTAL TESTS (8 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeveloperPortal(BaseTestCase):
    """Developer API Gateway & Webhook endpoints"""

    def test_create_api_key(self):
        res = self.client.post("/api/developer/keys", json={
            "key_name": "Test Production Key",
            "rate_limit": 100,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("raw_api_key", data)
        self.assertTrue(data["raw_api_key"].startswith("eiq_live_"))

    def test_list_api_keys(self):
        self.client.post("/api/developer/keys", json={
            "key_name": "List Test Key",
        }, headers=self.headers)
        res = self.client.get("/api/developer/keys", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 1)

    def test_revoke_api_key(self):
        create_res = self.client.post("/api/developer/keys", json={
            "key_name": "Revoke Test Key",
        }, headers=self.headers)
        key_id = create_res.get_json()["id"]
        res = self.client.delete(f"/api/developer/keys/{key_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_revoke_nonexistent_key(self):
        res = self.client.delete("/api/developer/keys/fake-key-id", headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_create_webhook_subscription(self):
        res = self.client.post("/api/developer/webhooks", json={
            "target_url": "https://api.example.com/webhooks",
            "events": ["meeting.created", "recording.ready"],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("secret_token", data)
        self.assertTrue(data["secret_token"].startswith("whsec_"))

    def test_create_webhook_missing_url(self):
        res = self.client.post("/api/developer/webhooks", json={
            "events": ["meeting.created"],
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_list_webhooks(self):
        self.client.post("/api/developer/webhooks", json={
            "target_url": "https://api.test.com/hooks",
        }, headers=self.headers)
        res = self.client.get("/api/developer/webhooks", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("subscriptions", data)
        self.assertIn("delivery_logs", data)

    def test_trigger_test_webhook(self):
        self.client.post("/api/developer/webhooks", json={
            "target_url": "https://httpbin.org/post",
        }, headers=self.headers)
        res = self.client.post("/api/developer/webhooks/test", json={
            "event": "meeting.created",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SECURITY & DLP TESTS (8 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurity(BaseTestCase):
    """Enterprise Security Governance & DLP endpoints"""

    def test_get_audit_logs(self):
        res = self.client.get("/api/security/audit-logs", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_add_ip_rule(self):
        res = self.client.post("/api/security/ip-rules", json={
            "cidr_range": "10.0.0.0/16",
            "description": "Office Subnet",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["cidr_range"], "10.0.0.0/16")

    def test_add_ip_rule_missing_cidr(self):
        res = self.client.post("/api/security/ip-rules", json={
            "description": "No CIDR",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_list_ip_rules(self):
        self.client.post("/api/security/ip-rules", json={
            "cidr_range": "192.168.1.0/24",
        }, headers=self.headers)
        res = self.client.get("/api/security/ip-rules", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.get_json()) >= 1)

    def test_revoke_session(self):
        user2_id = self._create_second_user()
        res = self.client.post("/api/security/revoke-session", json={
            "user_id": user2_id,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_revoke_session_missing_user(self):
        res = self.client.post("/api/security/revoke-session", json={}, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_dlp_scan_clean(self):
        res = self.client.post("/api/security/dlp-scan", json={
            "text_content": "This is a clean sentence with no sensitive data.",
            "source": "chat_message",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["is_clean"])

    def test_dlp_scan_detects_ssn(self):
        res = self.client.post("/api/security/dlp-scan", json={
            "text_content": "My SSN is 123-45-6789 please save it",
            "source": "file_upload",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data["is_clean"])
        self.assertTrue(len(data["offenses"]) >= 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. RECORDINGS TESTS (5 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecordings(BaseTestCase):
    """Meeting Recordings & HLS Streaming endpoints"""

    def _create_meeting_code(self):
        res = self.client.post("/api/v1/meetings", json={
            "title": "Recording Test",
        }, headers=self.headers)
        return res.get_json()["meeting"]["meeting_code"]

    def test_start_recording(self):
        code = self._create_meeting_code()
        res = self.client.post("/api/recordings/start", json={
            "meeting_code": code,
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["status"], "processing")

    def test_start_recording_missing_code(self):
        res = self.client.post("/api/recordings/start", json={}, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_list_recordings(self):
        code = self._create_meeting_code()
        self.client.post("/api/recordings/start", json={
            "meeting_code": code,
        }, headers=self.headers)
        res = self.client.get(f"/api/recordings/meeting/{code}", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_get_nonexistent_recording(self):
        res = self.client.get("/api/recordings/fake-rec-id", headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_stop_recording_no_active(self):
        res = self.client.post("/api/recordings/stop", json={
            "meeting_code": "no-active-recording",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. NOTIFICATIONS TESTS (6 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotifications(BaseTestCase):
    """Notifications endpoints"""

    def _create_notification(self):
        with self.app.app_context():
            notif = Notification(
                user_id=self.user_id,
                type="system_alert",
                title="Test Alert",
                body="You have a new update.",
            )
            db.session.add(notif)
            db.session.commit()
            return notif.id

    def test_list_notifications(self):
        self._create_notification()
        res = self.client.get("/api/v1/notifications", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("notifications", data)
        self.assertIn("unread_count", data)

    def test_mark_read(self):
        notif_id = self._create_notification()
        res = self.client.put(f"/api/v1/notifications/{notif_id}/read", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_mark_read_nonexistent(self):
        res = self.client.put("/api/v1/notifications/fake-id/read", headers=self.headers)
        self.assertEqual(res.status_code, 404)

    def test_mark_all_read(self):
        self._create_notification()
        self._create_notification()
        res = self.client.put("/api/v1/notifications/read-all", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_send_notification(self):
        user2_id = self._create_second_user()
        res = self.client.post("/api/v1/notifications/send", json={
            "recipient_id": user2_id,
            "notif_type": "meeting_invite",
            "title": "Meeting Reminder",
            "body": "Your meeting starts in 10 minutes.",
        }, headers=self.headers)
        self.assertEqual(res.status_code, 201)

    def test_send_notification_missing_fields(self):
        res = self.client.post("/api/v1/notifications/send", json={
            "body": "No recipient or title",
        }, headers=self.headers)
        self.assertIn(res.status_code, [400, 422])


# ═══════════════════════════════════════════════════════════════════════════════
# 10. DASHBOARD TESTS (3 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboard(BaseTestCase):
    """Dashboard overview endpoint"""

    def test_dashboard_overview(self):
        res = self.client.get("/api/v1/dashboard/overview", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("stats", data)
        self.assertIn("todays_meetings", data)
        self.assertIn("upcoming_meetings", data)
        self.assertIn("notifications", data)
        self.assertIn("recent_activity", data)

    def test_dashboard_overview_unauthenticated(self):
        anon_client = self.app.test_client()
        res = anon_client.get("/api/v1/dashboard/overview")
        self.assertIn(res.status_code, [401, 422])

    def test_dashboard_stats_structure(self):
        res = self.client.get("/api/v1/dashboard/overview", headers=self.headers)
        stats = res.get_json()["stats"]
        self.assertIn("hosted_count", stats)
        self.assertIn("joined_count", stats)
        self.assertIn("total_minutes", stats)
        self.assertIn("unread_notifications", stats)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. HEALTH & READINESS TESTS (4 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealth(BaseTestCase):
    """Health check and readiness probe endpoints"""

    def test_index_welcome(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "online")

    def test_liveness_probe(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ok")

    def test_readiness_probe(self):
        res = self.client.get("/api/v1/ready")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ready")

    def test_nonexistent_route(self):
        res = self.client.get("/api/v1/nonexistent")
        self.assertEqual(res.status_code, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. FILES TESTS (5 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFiles(BaseTestCase):
    """File upload and management endpoints"""

    def test_upload_file(self):
        data = {
            "file": (io.BytesIO(b"Hello ElevateIQ"), "test_document.txt"),
        }
        res = self.client.post(
            "/api/v1/files/upload",
            data=data,
            content_type="multipart/form-data",
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 201)
        self.assertIn("file", res.get_json())

    def test_upload_no_file(self):
        res = self.client.post(
            "/api/v1/files/upload",
            data={},
            content_type="multipart/form-data",
            headers=self.headers,
        )
        self.assertIn(res.status_code, [400, 422])

    def test_list_files(self):
        # Upload a file first
        self.client.post(
            "/api/v1/files/upload",
            data={"file": (io.BytesIO(b"content"), "file.txt")},
            content_type="multipart/form-data",
            headers=self.headers,
        )
        res = self.client.get("/api/v1/files", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("files", res.get_json())

    def test_delete_file(self):
        upload_res = self.client.post(
            "/api/v1/files/upload",
            data={"file": (io.BytesIO(b"delete me"), "delete.txt")},
            content_type="multipart/form-data",
            headers=self.headers,
        )
        file_id = upload_res.get_json()["file"]["id"]
        res = self.client.delete(f"/api/v1/files/{file_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)

    def test_delete_nonexistent_file(self):
        res = self.client.delete("/api/v1/files/fake-file-id", headers=self.headers)
        self.assertEqual(res.status_code, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# 13. DLP SCANNER SERVICE UNIT TESTS (5 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDLPScannerUnit(unittest.TestCase):
    """Direct unit tests for DLPScannerService class"""

    def test_scan_clean_text(self):
        from backend.services.dlp_scanner import DLPScannerService
        result = DLPScannerService.scan_text("This is a perfectly clean document.")
        self.assertTrue(result["is_clean"])
        self.assertEqual(len(result["offenses"]), 0)

    def test_scan_ssn_detection(self):
        from backend.services.dlp_scanner import DLPScannerService
        result = DLPScannerService.scan_text("SSN: 123-45-6789")
        self.assertFalse(result["is_clean"])

    def test_scan_credit_card_detection(self):
        from backend.services.dlp_scanner import DLPScannerService
        result = DLPScannerService.scan_text("Card: 4111111111111111")
        self.assertFalse(result["is_clean"])

    def test_scan_private_key_detection(self):
        from backend.services.dlp_scanner import DLPScannerService
        result = DLPScannerService.scan_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEvAIBAD...")
        self.assertFalse(result["is_clean"])

    def test_scan_empty_text(self):
        from backend.services.dlp_scanner import DLPScannerService
        result = DLPScannerService.scan_text("")
        self.assertTrue(result["is_clean"])


if __name__ == "__main__":
    unittest.main()
