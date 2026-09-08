"""
ElevateIQ — Unit Test Suite for LDAP Directory Sync Engine
==========================================================
Tests LDAP directory delta sync execution, created/updated user metrics, and sync history.
"""

import unittest
from backend.services.enterprise.directory_sync_engine import DirectorySyncEngine


class DirectorySyncTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = DirectorySyncEngine(ldap_host="ldap.stark.com")

    def test_directory_sync_execution(self):
        """Test executing LDAP directory synchronization."""
        res = self.engine.perform_directory_sync("tenant_stark_101", simulated_entries_count=100)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["tenant_id"], "tenant_stark_101")
        self.assertEqual(res["users_created"], 20)
        self.assertEqual(res["users_updated"], 70)

        last = self.engine.get_last_sync_status("tenant_stark_101")
        self.assertIsNotNone(last)
        self.assertEqual(last["sync_id"], res["sync_id"])


if __name__ == "__main__":
    unittest.main()
