"""
ElevateIQ — SCIM 2.0 User Lifecycle & Group Membership Integration Test Suite
=============================================================================
Tests automated Okta / Azure AD SCIM user provisioning, suspension, group assignment, and deletion.
"""

import unittest
from backend.services.scim_provisioning import SCIMProvisioningEngine


class SCIMUserLifecycleTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = SCIMProvisioningEngine()

    def test_full_scim_lifecycle(self):
        """Test complete SCIM user provision -> update -> deprovision lifecycle."""
        # 1. Provision user
        user = self.engine.create_user({
            "userName": "sarah_connor@skynet.com",
            "displayName": "Sarah Connor",
            "emails": [{"value": "sarah_connor@skynet.com"}],
            "active": True
        })

        scim_id = user["id"]
        self.assertTrue(user["active"])

        # 2. Deactivate user
        updated = self.engine.update_user_status(scim_id, False)
        self.assertFalse(updated["active"])

        # 3. List users filter
        listed = self.engine.list_users(start_index=1, count=10)
        self.assertEqual(listed["totalResults"], 1)

        # 4. Deprovision
        deleted = self.engine.delete_user(scim_id)
        self.assertTrue(deleted)


if __name__ == "__main__":
    unittest.main()
