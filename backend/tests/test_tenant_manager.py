"""
ElevateIQ — Unit Test Suite for Multi-Tenant Manager & RBAC Engine
====================================================================
Tests enterprise tenant registration, domain lookup, IP whitelist policies,
and fine-grained RBAC permission matrix evaluations.
"""

import unittest
from backend.services.enterprise.tenant_manager import TenantManagerService
from backend.services.enterprise.rbac_engine import RBACPolicyEvaluator


class EnterpriseTenantTestSuite(unittest.TestCase):

    def setUp(self):
        self.tenant_service = TenantManagerService()
        self.rbac_evaluator = RBACPolicyEvaluator()

    def test_organization_creation_and_domain_lookup(self):
        """Test creating enterprise tenant organization and domain mapping."""
        org = self.tenant_service.create_organization("Acme Corp", "acme.com", max_users=1000)
        self.assertEqual(org.name, "Acme Corp")
        self.assertEqual(org.domain, "acme.com")

        found_org = self.tenant_service.get_organization_by_domain("acme.com")
        self.assertIsNotNone(found_org)
        self.assertEqual(found_org.org_id, org.org_id)

    def test_ip_whitelist_validation(self):
        """Test IP CIDR whitelist verification."""
        org = self.tenant_service.create_organization("Beta Inc", "beta.io")
        self.tenant_service.set_ip_whitelist(org.org_id, ["192.168.1.0/24"])

        self.assertTrue(self.tenant_service.validate_ip_access(org.org_id, "192.168.1.50"))
        self.assertFalse(self.tenant_service.validate_ip_access(org.org_id, "10.0.0.1"))

    def test_rbac_permission_evaluation(self):
        """Test role-based access control permission checks."""
        self.assertTrue(self.rbac_evaluator.evaluate_permission(["host"], "meeting:create"))
        self.assertTrue(self.rbac_evaluator.evaluate_permission(["super_admin"], "compliance:export"))
        self.assertFalse(self.rbac_evaluator.evaluate_permission(["guest"], "meeting:create"))

    def test_rbac_grant_and_revoke(self):
        """Test dynamic granting and revoking of permissions."""
        self.rbac_evaluator.grant_permission_to_role("participant", "meeting:record")
        self.assertTrue(self.rbac_evaluator.evaluate_permission(["participant"], "meeting:record"))

        self.rbac_evaluator.revoke_permission_from_role("participant", "meeting:record")
        self.assertFalse(self.rbac_evaluator.evaluate_permission(["participant"], "meeting:record"))


if __name__ == "__main__":
    unittest.main()
