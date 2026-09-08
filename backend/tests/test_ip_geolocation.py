"""
ElevateIQ — Unit Test Suite for IP Geolocation & Geofencing Resolver
====================================================================
Tests IP country lookup and geofence evaluation.
"""

import unittest
from backend.services.enterprise.ip_geolocation_service import IPGeolocationService


class IPGeolocationTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = IPGeolocationService()

    def test_internal_ip_resolution(self):
        """Test internal IP address resolution."""
        res = self.service.resolve_ip("192.168.1.50")
        self.assertEqual(res["country_code"], "US")

    def test_geofence_policy_evaluation(self):
        """Test geographic country whitelist policy enforcement."""
        self.assertTrue(self.service.evaluate_geofence_policy("192.168.1.1", ["US", "CA"]))
        self.assertFalse(self.service.evaluate_geofence_policy("8.8.8.8", ["GB", "DE"]))


if __name__ == "__main__":
    unittest.main()
