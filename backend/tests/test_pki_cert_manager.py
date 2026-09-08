"""
ElevateIQ — Unit Test Suite for Custom TLS Certificate Manager
==============================================================
Tests certificate registration and renewal health checks.
"""

import unittest
from backend.services.enterprise.pki_cert_manager import PKICertificateManager


class PKICertificateManagerTestSuite(unittest.TestCase):

    def setUp(self):
        self.manager = PKICertificateManager()

    def test_register_and_health_check(self):
        """Test registering TLS certificate and checking health status."""
        cert = self.manager.register_certificate("meet.stark.com", "CERT_PEM", "KEY_PEM")
        self.assertEqual(cert["domain_name"], "meet.stark.com")

        health = self.manager.check_certificate_health("meet.stark.com")
        self.assertEqual(health["status"], "HEALTHY")
        self.assertGreater(health["days_remaining"], 30)


if __name__ == "__main__":
    unittest.main()
