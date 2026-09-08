"""
ElevateIQ — Unit Test Suite for SCIM 2.0 Identity Provisioning Protocol
========================================================================
Tests SCIM user creation, activation status updates, deprovisioning, and listing.
"""

import unittest
from backend.services.scim_provisioning import SCIMProvisioningEngine


class SCIMProvisioningTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = SCIMProvisioningEngine()

    def test_scim_user_creation(self):
        """Test provisioning a user account via SCIM 2.0 POST payload."""
        payload = {
            "userName": "david_scim@acme.com",
            "name": {"givenName": "David", "familyName": "Miller"},
            "displayName": "David Miller",
            "emails": [{"value": "david_scim@acme.com", "primary": True}],
            "active": True,
        }

        user = self.engine.create_user(payload)
        self.assertTrue(user["id"].startswith("scim_usr_"))
        self.assertEqual(user["userName"], "david_scim@acme.com")
        self.assertTrue(user["active"])

    def test_scim_user_status_update_and_deletion(self):
        """Test deactivating and deleting a SCIM user."""
        user = self.engine.create_user({"userName": "temp@acme.com"})
        scim_id = user["id"]

        updated = self.engine.update_user_status(scim_id, False)
        self.assertFalse(updated["active"])

        deleted = self.engine.delete_user(scim_id)
        self.assertTrue(deleted)

    def test_scim_list_users(self):
        """Test SCIM GET /Users listing with pagination."""
        for i in range(5):
            self.engine.create_user({"userName": f"user{i}@acme.com"})

        resp = self.engine.list_users(start_index=1, count=10)
        self.assertEqual(resp["totalResults"], 5)
        self.assertEqual(len(resp["Resources"]), 5)


if __name__ == "__main__":
    unittest.main()
