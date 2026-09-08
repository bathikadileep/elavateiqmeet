"""
ElevateIQ — Unit Test Suite for Compliance Data Export Service
==============================================================
Tests creating GDPR DSAR encrypted export ZIP packages.
"""

import unittest
import os
from backend.services.enterprise.compliance_export_service import ComplianceExportService


class ComplianceExportPackageTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = ComplianceExportService(export_dir="compliance_exports_test")

    def test_dsar_export_generation(self):
        """Test bundling DSAR archive package into ZIP file."""
        pkg = self.service.generate_dsar_export_package(
            user_id="usr_gdpr_101",
            user_email="gdpr@enterprise.com",
            meeting_codes=["room-101", "room-102"]
        )

        self.assertTrue(pkg["export_id"].startswith("dsar_"))
        self.assertTrue(os.path.exists(pkg["zip_filepath"]))
        self.assertGreater(pkg["file_size_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
