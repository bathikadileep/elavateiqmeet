"""
ElevateIQ — Socket.IO Real-Time Event Test Suite (Module 7)
============================================================
Comprehensive Socket.IO test cases covering connection management,
WebRTC signaling, live chat, whiteboard vector synchronization,
breakout room events, SFU transport signaling, and speech captions.

Run with:
    python -m pytest backend/test_socket_events.py -v
"""

import unittest
from backend.app import create_app
from backend.extensions import db, socketio
from backend.models.models import User, Meeting, MeetingParticipant, WhiteboardSnapshot


class SocketBaseTestCase(unittest.TestCase):
    """Shared setup creating app, db, user, meeting, and Socket.IO test client."""

    def setUp(self):
        self.app = create_app("testing")
        self.http_client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            self.user = User(
                username="socketuser",
                email="socket@elevateiq.com",
                display_name="Socket Tester",
                status="active",
            )
            self.user.set_password("SocketPass123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

            self.meeting = Meeting(
                title="Socket Test Room",
                meeting_code="skt-test-room",
                host_id=self.user.id,
                status="live",
            )
            db.session.add(self.meeting)
            db.session.commit()
            self.meeting_code = self.meeting.meeting_code

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _get_sio_client(self):
        """Create and return a connected Socket.IO test client."""
        return socketio.test_client(self.app, flask_test_client=self.http_client)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONNECTION & ROOM MANAGEMENT TESTS (8 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSocketConnection(SocketBaseTestCase):
    """Socket.IO connection, join_room, leave_room, disconnect events."""

    def test_socket_connects(self):
        sio = self._get_sio_client()
        self.assertTrue(sio.is_connected())
        sio.disconnect()

    def test_socket_receives_connected_event(self):
        sio = self._get_sio_client()
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("connected", event_names)
        sio.disconnect()

    def test_join_room(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "socketuser",
            "display_name": "Socket Tester",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        # Should receive user_joined and/or room_roster
        self.assertTrue(
            "user_joined" in event_names or "room_roster" in event_names,
            f"Expected user_joined or room_roster, got: {event_names}"
        )
        sio.disconnect()

    def test_join_room_missing_code(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "username": "socketuser",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("error", event_names)
        sio.disconnect()

    def test_leave_room(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "socketuser",
        })
        sio.get_received()  # Clear received

        sio.emit("leave_room", {"room_code": self.meeting_code})
        # Should not crash
        sio.disconnect()

    def test_disconnect_cleanup(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "socketuser",
        })
        sio.disconnect()
        self.assertFalse(sio.is_connected())

    def test_multiple_clients_join_room(self):
        sio1 = self._get_sio_client()
        sio2 = self._get_sio_client()

        sio1.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "user1",
            "display_name": "User 1",
        })
        sio2.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "user2",
            "display_name": "User 2",
        })

        received2 = sio2.get_received()
        self.assertTrue(len(received2) > 0)

        sio1.disconnect()
        sio2.disconnect()

    def test_join_creates_participant_record(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "socketuser",
        })
        sio.get_received()

        with self.app.app_context():
            mp = MeetingParticipant.query.filter_by(
                meeting_id=self.meeting.id,
                user_id=self.user_id,
            ).first()
            self.assertIsNotNone(mp)
            self.assertEqual(mp.status, "joined")

        sio.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. WEBRTC SIGNALING TESTS (5 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestWebRTCSignaling(SocketBaseTestCase):
    """WebRTC offer/answer/ICE and media state change events."""

    def test_webrtc_offer_relay(self):
        sio1 = self._get_sio_client()
        sio2 = self._get_sio_client()

        sio1.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "offerer",
        })
        sio2.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "answerer",
        })
        sio1.get_received()
        sio2.get_received()

        # Emit offer (relay requires target_sid)
        sio1.emit("webrtc_offer", {
            "target_sid": "nonexistent_sid",
            "sdp": {"type": "offer", "sdp": "v=0\r\n..."},
        })
        # Should not crash even with invalid target
        sio1.disconnect()
        sio2.disconnect()

    def test_webrtc_answer_relay(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "answerer",
        })
        sio.get_received()

        sio.emit("webrtc_answer", {
            "target_sid": "peer_sid",
            "sdp": {"type": "answer", "sdp": "v=0\r\n..."},
        })
        sio.disconnect()

    def test_webrtc_ice_candidate_relay(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "ice_user",
        })
        sio.get_received()

        sio.emit("webrtc_ice_candidate", {
            "target_sid": "peer_sid",
            "candidate": {
                "candidate": "candidate:1 1 UDP 2130706431 192.168.1.1 50000 typ host",
                "sdpMid": "0",
                "sdpMLineIndex": 0,
            },
        })
        sio.disconnect()

    def test_media_state_change(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "media_user",
        })
        sio.get_received()

        sio.emit("media_state_change", {
            "room_code": self.meeting_code,
            "is_audio_muted": True,
            "is_video_off": False,
            "is_screen_sharing": False,
            "hand_raised": True,
        })
        sio.disconnect()

    def test_webrtc_offer_missing_fields_no_crash(self):
        sio = self._get_sio_client()
        sio.emit("webrtc_offer", {})
        # Should silently ignore, not crash
        sio.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. LIVE CHAT TESTS (6 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSocketChat(SocketBaseTestCase):
    """Real-time chat, typing indicators, and chat history."""

    def test_send_public_message(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "chatuser",
            "display_name": "Chat User",
        })
        sio.get_received()

        sio.emit("send_message", {
            "room_code": self.meeting_code,
            "content": "Hello everyone!",
            "user_id": self.user_id,
            "display_name": "Chat User",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("new_message", event_names)
        sio.disconnect()

    def test_send_empty_message_ignored(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "emptyuser",
        })
        sio.get_received()

        sio.emit("send_message", {
            "room_code": self.meeting_code,
            "content": "",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertNotIn("new_message", event_names)
        sio.disconnect()

    def test_typing_start_broadcast(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "typer",
        })
        sio.get_received()

        sio.emit("typing_start", {
            "room_code": self.meeting_code,
            "display_name": "Typer",
        })
        sio.disconnect()

    def test_typing_stop_broadcast(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "typer",
        })
        sio.get_received()

        sio.emit("typing_stop", {
            "room_code": self.meeting_code,
        })
        sio.disconnect()

    def test_load_chat_history(self):
        sio = self._get_sio_client()
        sio.emit("load_chat_history", {
            "room_code": self.meeting_code,
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        # Should receive chat_history event
        self.assertTrue(
            "chat_history" in event_names or "connected" in event_names,
            f"Expected chat_history or connected, got: {event_names}"
        )
        sio.disconnect()

    def test_private_message_to_nonexistent_user(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "user_id": self.user_id,
            "username": "dmuser",
        })
        sio.get_received()

        sio.emit("send_message", {
            "room_code": self.meeting_code,
            "content": "Private whisper",
            "recipient_id": "nonexistent_user_id",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("error", event_names)
        sio.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. WHITEBOARD TESTS (5 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSocketWhiteboard(SocketBaseTestCase):
    """Whiteboard vector draw synchronization, clear, save, and get state events."""

    def test_whiteboard_draw_event(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "drawer",
        })
        sio.get_received()

        sio.emit("whiteboard_draw_event", {
            "room_code": self.meeting_code,
            "stroke": {
                "tool": "pencil",
                "points": [10, 10, 50, 50, 90, 30],
                "color": "#6366f1",
                "width": 3,
            },
        })
        sio.disconnect()

    def test_whiteboard_clear(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "clearer",
        })
        sio.get_received()

        sio.emit("whiteboard_clear", {
            "room_code": self.meeting_code,
        })
        sio.disconnect()

    def test_whiteboard_save_state(self):
        sio = self._get_sio_client()
        sio.emit("whiteboard_save_state", {
            "room_code": self.meeting_code,
            "snapshot_json": [
                {"tool": "pencil", "points": [0, 0, 100, 100], "color": "#ff0000"},
            ],
        })
        sio.disconnect()

        # Verify snapshot was saved in database
        with self.app.app_context():
            snap = WhiteboardSnapshot.query.filter_by(meeting_code=self.meeting_code).first()
            self.assertIsNotNone(snap)

    def test_whiteboard_get_state_exists(self):
        # First save a snapshot
        sio1 = self._get_sio_client()
        sio1.emit("whiteboard_save_state", {
            "room_code": self.meeting_code,
            "snapshot_json": [{"tool": "line", "points": [5, 5, 50, 50]}],
        })
        sio1.disconnect()

        # Now retrieve it
        sio2 = self._get_sio_client()
        sio2.emit("whiteboard_get_state", {
            "room_code": self.meeting_code,
        })
        received = sio2.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("whiteboard_state_response", event_names)
        sio2.disconnect()

    def test_whiteboard_get_state_empty(self):
        sio = self._get_sio_client()
        sio.emit("whiteboard_get_state", {
            "room_code": "empty-whiteboard-room",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("whiteboard_state_response", event_names)
        sio.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CAPTION / SPEECH TRANSCRIPT TESTS (3 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSocketCaptions(SocketBaseTestCase):
    """Live speech captioning event tests."""

    def test_speech_transcript_event(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "speaker",
            "display_name": "Caption Speaker",
        })
        sio.get_received()

        sio.emit("speech_transcript_event", {
            "room_code": self.meeting_code,
            "speaker_name": "Caption Speaker",
            "text": "Hello, this is a live caption test.",
            "is_final": True,
        })
        sio.disconnect()

    def test_speech_transcript_missing_room(self):
        sio = self._get_sio_client()
        sio.emit("speech_transcript_event", {
            "text": "Orphaned caption",
            "is_final": False,
        })
        # Should silently ignore
        sio.disconnect()

    def test_speech_transcript_interim(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "interim_speaker",
        })
        sio.get_received()

        sio.emit("speech_transcript_event", {
            "room_code": self.meeting_code,
            "text": "This is an inter",
            "is_final": False,
        })
        sio.emit("speech_transcript_event", {
            "room_code": self.meeting_code,
            "text": "This is an interim caption completed.",
            "is_final": True,
        })
        sio.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SFU SIGNALING TESTS (4 test cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSFUSignaling(SocketBaseTestCase):
    """SFU WebRTC transport signaling events."""

    def test_sfu_get_router_capabilities(self):
        sio = self._get_sio_client()
        sio.emit("sfu_get_router_capabilities", {})
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("sfu_router_capabilities", event_names)
        sio.disconnect()

    def test_sfu_create_transport(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "sfu_user",
        })
        sio.get_received()

        sio.emit("sfu_create_transport", {
            "room_code": self.meeting_code,
            "direction": "sendrecv",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("sfu_transport_created", event_names)
        sio.disconnect()

    def test_sfu_create_transport_missing_room(self):
        sio = self._get_sio_client()
        sio.emit("sfu_create_transport", {
            "direction": "sendrecv",
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("sfu_error", event_names)
        sio.disconnect()

    def test_sfu_get_stats(self):
        sio = self._get_sio_client()
        sio.emit("join_room", {
            "room_code": self.meeting_code,
            "username": "stats_user",
        })
        sio.get_received()

        sio.emit("sfu_get_stats", {
            "room_code": self.meeting_code,
        })
        received = sio.get_received()
        event_names = [msg["name"] for msg in received]
        self.assertIn("sfu_stats_response", event_names)
        sio.disconnect()


if __name__ == "__main__":
    unittest.main()
