"""
ElevateIQ — Unit & Integration Test Suite for Fine-Grained RBAC Engine
======================================================================
Tests role permission evaluation, granting, revoking, and privilege matrix.
"""

import unittest
from backend.services.enterprise.rbac_engine import RBACPolicyEvaluator


class RBACPermissionsTestSuite(unittest.TestCase):

    def setUp(self):
        self.evaluator = RBACPolicyEvaluator()

    def test_permission_grant_and_revocation(self):
        """Test granting and revoking role permissions."""
        self.evaluator.grant_permission_to_role("participant", "meeting:custom_action")
        self.assertTrue(self.evaluator.evaluate_permission(["participant"], "meeting:custom_action"))

        self.evaluator.revoke_permission_from_role("participant", "meeting:custom_action")
        self.assertFalse(self.evaluator.evaluate_permission(["participant"], "meeting:custom_action"))

    def test_role_hierarchy_evaluation(self):
        """Test role matrix permissions evaluation for host vs guest."""
        self.assertTrue(self.evaluator.evaluate_permission(["host"], "meeting:mute_all"))
        self.assertFalse(self.evaluator.evaluate_permission(["guest"], "meeting:mute_all"))


if __name__ == "__main__":
    unittest.main()
