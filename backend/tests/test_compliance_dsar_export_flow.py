"""
ElevateIQ — Compliance DSAR Export Package Integration Test Suite
==================================================================
Tests bundling user transcript histories into encrypted ZIP packages for GDPR Right of Access requests.
"""

import unittest
import os
from backend.services.enterprise.compliance_export_service import ComplianceExportService


class ComplianceDSARExportFlowTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = ComplianceExportService(export_dir="dsar_exports_flow_test")

    def test_dsar_package_bundling(self):
        """Test packaging user data into ZIP file."""
        pkg = self.service.generate_dsar_export_package("user_gdpr_202", "user202@enterprise.com", ["room-a", "room-b"])
        self.assertTrue(os.path.exists(pkg["zip_filepath"]))
        self.assertGreater(pkg["file_size_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
