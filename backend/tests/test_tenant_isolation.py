"""
ElevateIQ — Unit & Integration Test Suite for Multi-Tenant Isolation
======================================================================
Tests organization tenant registration, domain resolving, and IP whitelist policies.
"""

import unittest
from backend.services.enterprise.tenant_manager import TenantManagerService


class TenantIsolationTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = TenantManagerService()

    def test_create_organization_and_lookup(self):
        """Test creating enterprise organization tenant and domain lookup."""
        org = self.service.create_organization("Stark Industries", "stark.com", max_users=500)
        self.assertEqual(org.name, "Stark Industries")

        fetched = self.service.get_organization_by_domain("stark.com")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.org_id, org.org_id)

    def test_ip_whitelist_validation(self):
        """Test enterprise tenant IP CIDR range enforcement."""
        org = self.service.create_organization("Wayne Enterprises", "wayne.com")
        self.service.set_ip_whitelist(org.org_id, ["192.168.1.0/24"])

        self.assertTrue(self.service.validate_ip_access(org.org_id, "192.168.1.45"))
        self.assertFalse(self.service.validate_ip_access(org.org_id, "10.0.0.1"))


if __name__ == "__main__":
    unittest.main()
