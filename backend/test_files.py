"""
ElevateIQ — File Sharing Unit Tests
====================================
Tests file management endpoints:
  1. Upload single file
  2. List uploaded files
  3. Preview & Download file
  4. Delete file
"""

import io
import unittest
from backend.app import create_app
from backend.extensions import db

class FilesTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

        # Register & Login User
        self.client.post("/api/v1/auth/register", json={
            "username": "fileuser",
            "email": "file@example.com",
            "password": "password123"
        })
        self.client.post("/api/v1/auth/login", json={
            "identity": "fileuser",
            "password": "password123"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_file_upload_list_download_delete(self):
        # 1. Upload File
        data = {
            "file": (io.BytesIO(b"Hello ElevateIQ File Storage"), "test_agenda.txt"),
            "file_category": "attachment",
        }
        res = self.client.post("/api/v1/files/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 201)
        file_info = res.get_json()["file"]
        file_id = file_info["id"]
        self.assertEqual(file_info["original_name"], "test_agenda.txt")

        # 2. List Files
        list_res = self.client.get("/api/v1/files")
        self.assertEqual(list_res.status_code, 200)
        files = list_res.get_json()["files"]
        self.assertEqual(len(files), 1)

        # 3. Preview / Download
        preview_res = self.client.get(f"/api/v1/files/{file_id}/preview")
        self.assertEqual(preview_res.status_code, 200)
        self.assertEqual(preview_res.data, b"Hello ElevateIQ File Storage")

        # 4. Delete File
        del_res = self.client.delete(f"/api/v1/files/{file_id}")
        self.assertEqual(del_res.status_code, 200)

        # Confirm deleted from list
        list_res2 = self.client.get("/api/v1/files")
        self.assertEqual(len(list_res2.get_json()["files"]), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
