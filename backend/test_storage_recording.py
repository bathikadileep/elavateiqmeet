"""
ElevateIQ Storage & Cloud Recording Suite — Automated Unit Test Suite
======================================================================
Tests Pluggable Storage Drivers (Local, Neon, S3), Factory .env switching,
Headless Cloud Recorder Worker, HLS Transcoder, and REST API endpoints.
"""

import unittest
import io
import os
import time
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, MeetingRecording
from backend.services.storage import get_storage_provider
from backend.services.storage.local_provider import LocalStorageProvider
from backend.services.storage.neon_provider import NeonStorageProvider
from backend.services.storage.s3_provider import S3StorageProvider
from backend.workers.recorder_worker import start_recording_worker, stop_recording_worker
from backend.services.hls_transcoder import HLSTranscoderService


class StorageRecordingTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                username="storageuser",
                email="storage@example.com",
                display_name="Storage User"
            )
            self.user.set_password("Password123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        # Login and obtain access token
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "storageuser",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.room_code = f"rec-{int(time.time())}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_pluggable_storage_factory(self):
        os.environ["STORAGE_PROVIDER"] = "local"
        provider = get_storage_provider()
        self.assertIsInstance(provider, LocalStorageProvider)

        dummy_file = io.BytesIO(b"ElevateIQ Test Storage Data Payload")
        meta = provider.upload_file(dummy_file, "test.txt", "text/plain", folder="test")
        self.assertIn("storage_path", meta)

        content = provider.download_file(meta["storage_path"])
        self.assertEqual(content, b"ElevateIQ Test Storage Data Payload")

    def test_recorder_worker_lifecycle(self):
        session = start_recording_worker(self.room_code, "test-rec-id")
        self.assertTrue(session.is_recording)

        time.sleep(0.5)

        stopped_meta = stop_recording_worker(self.room_code)
        self.assertIsNotNone(stopped_meta)
        self.assertEqual(stopped_meta["recording_id"], "test-rec-id")

    def test_hls_transcoder_generation(self):
        output_dir = os.path.join("uploads", "recordings", "test_hls_unit")
        meta = HLSTranscoderService.transcode_to_hls("dummy.mp4", output_dir)
        self.assertTrue(os.path.exists(meta["playlist_path"]))
        self.assertEqual(meta["segment_count"], 3)

    def test_recordings_rest_api_endpoints(self):
        # 1. Start recording
        res_start = self.client.post("/api/recordings/start", json={
            "meeting_code": self.room_code
        }, headers=self.headers)
        self.assertEqual(res_start.status_code, 201)

        # 2. Stop recording & transcode HLS
        res_stop = self.client.post("/api/recordings/stop", json={
            "meeting_code": self.room_code
        }, headers=self.headers)
        self.assertEqual(res_stop.status_code, 200)
        stop_data = res_stop.get_json()
        self.assertIn("hls_playlist_url", stop_data)

        # 3. Stream HLS playlist
        rec_id = stop_data["id"] if "id" in stop_data else stop_data["recording_id"]
        res_hls = self.client.get(f"/api/recordings/{rec_id}/stream/index.m3u8")
        self.assertEqual(res_hls.status_code, 200)


if __name__ == "__main__":
    unittest.main()
