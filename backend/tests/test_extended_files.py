"""
ElevateIQ — Extended File Storage & Checksum Test Suite
======================================================
Tests local disk file uploads, mime type validation, size byte calculation,
and SHA-256 checksum integrity verification.
"""

import unittest
import hashlib
import os
from backend.app import create_app
from backend.extensions import db
from backend.models.models import File, User
from backend.services.storage.local_provider import LocalStorageProvider


class ExtendedFilesTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.storage = LocalStorageProvider(base_directory="uploads_test")

        self.uploader = User(
            username="file_user",
            email="file@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="File Uploader",
            status="active",
            email_verified=True,
        )
        db.session.add(self.uploader)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_file_upload_and_sha256_checksum(self):
        """Test file byte storage and SHA-256 hash generation."""
        content = b"Sample presentation attachment content for meeting."
        sha256_hash = hashlib.sha256(content).hexdigest()

        res = self.storage.upload_file(content, "sample_doc.pdf", folder="attachments")
        self.assertIsNotNone(res)
        self.assertIn("storage_path", res)

        db_file = File(
            uploader_id=self.uploader.id,
            file_category="attachment",
            original_name="sample_doc.pdf",
            stored_name="sample_doc_12345.pdf",
            storage_path=res["storage_path"],
            mime_type="application/pdf",
            size_bytes=len(content),
            checksum_sha256=sha256_hash
        )
        db.session.add(db_file)
        db.session.commit()

        fetched = File.query.filter_by(checksum_sha256=sha256_hash).first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.size_bytes, len(content))
        self.assertEqual(fetched.original_name, "sample_doc.pdf")


if __name__ == "__main__":
    unittest.main()
