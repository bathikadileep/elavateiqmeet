"""
ElevateIQ — Unit Test Suite for SCIM 2.0 Group Manager
======================================================
Tests creating group resources and adding members.
"""

import unittest
from backend.services.enterprise.scim_group_manager import SCIMGroupManager


class SCIMGroupManagerTestSuite(unittest.TestCase):

    def setUp(self):
        self.manager = SCIMGroupManager()

    def test_create_group_and_add_member(self):
        """Test creating SCIM group and updating members list."""
        grp = self.manager.create_group("Engineering Team", member_ids=["usr_1", "usr_2"])
        self.assertEqual(grp["displayName"], "Engineering Team")
        self.assertEqual(len(grp["members"]), 2)

        updated = self.manager.add_member_to_group(grp["id"], "usr_3")
        self.assertEqual(len(updated["members"]), 3)


if __name__ == "__main__":
    unittest.main()
