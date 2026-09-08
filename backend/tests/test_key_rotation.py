"""
ElevateIQ — Unit Test Suite for Cryptographic Key Rotation Engine
===================================================================
Tests zero-downtime key rotation, active key retrieval, and key ring deprecation.
"""

import unittest
from backend.services.enterprise.key_rotation_service import KeyRotationEngine


class KeyRotationTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = KeyRotationEngine(rotation_interval_days=90)

    def test_key_generation_and_active_retrieval(self):
        """Test generating new cryptographic key version."""
        key1 = self.engine.generate_new_key("JWT_RS256")
        self.assertEqual(key1["status"], "ACTIVE")
        self.assertEqual(key1["version"], 1)

        active = self.engine.get_active_key("JWT_RS256")
        self.assertEqual(active["key_id"], key1["key_id"])

    def test_key_rotation_deprecation_lifecycle(self):
        """Test deprecating previous key when rotating to a new version."""
        key1 = self.engine.generate_new_key("DATABASE_DEK")
        key2 = self.engine.generate_new_key("DATABASE_DEK")

        self.assertEqual(key2["version"], 2)
        self.assertEqual(key2["status"], "ACTIVE")

        valid_keys = self.engine.get_valid_keys("DATABASE_DEK")
        self.assertEqual(len(valid_keys), 2)
        self.assertEqual(valid_keys[0]["status"], "DEPRECATED")


if __name__ == "__main__":
    unittest.main()
