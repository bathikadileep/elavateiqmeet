"""
ElevateIQ — Unit Tests for Data Residency & Sovereignty Router
================================================================
Tests sovereign edge cluster registration, tenant residency policy enforcement,
optimal regional cluster routing, cross-border transit blocking, and PII anonymization.
"""

import unittest
from backend.services.enterprise.data_residency_router import (
    DataResidencyRouter,
    SovereignRegion,
    EdgeCluster,
    TenantResidencyPolicy
)


class TestDataResidencyRouter(unittest.TestCase):

    def setUp(self):
        self.router = DataResidencyRouter()

        # Register German Bank tenant with strict EU_WEST residency
        self.router.register_tenant_policy(
            tenant_id="org_deutsche_bank",
            tenant_name="Deutsche Bank",
            primary_region=SovereignRegion.EU_WEST,
            allowed_regions={SovereignRegion.EU_WEST},
            strictly_enforced=True,
            allow_cross_border_fallback=False
        )

        # Register Global Corp tenant allowing US and EU
        self.router.register_tenant_policy(
            tenant_id="org_global_corp",
            tenant_name="Global Tech Corp",
            primary_region=SovereignRegion.US_EAST,
            allowed_regions={SovereignRegion.US_EAST, SovereignRegion.EU_WEST},
            strictly_enforced=False,
            allow_cross_border_fallback=True
        )

    def test_default_clusters_initialized(self):
        self.assertGreaterEqual(len(self.router.clusters), 7)
        self.assertIn("sfu-eu-de-1", self.router.clusters)
        self.assertIn("sfu-us-va-1", self.router.clusters)
        self.assertIn("sfu-ch-zh-1", self.router.clusters)

    def test_select_cluster_strict_eu_tenant(self):
        cluster = self.router.select_optimal_cluster("org_deutsche_bank")
        self.assertEqual(cluster.region, SovereignRegion.EU_WEST)
        self.assertIn(cluster.cluster_id, ("sfu-eu-de-1", "sfu-eu-ie-1"))

    def test_select_cluster_with_load_balancing(self):
        # Set higher load on Frankfurt, lower on Dublin
        self.router.clusters["sfu-eu-de-1"].load_factor = 0.85
        self.router.clusters["sfu-eu-ie-1"].load_factor = 0.15

        selected = self.router.select_optimal_cluster("org_deutsche_bank")
        self.assertEqual(selected.cluster_id, "sfu-eu-ie-1")

    def test_strict_residency_prohibits_unallowed_region(self):
        # Attempt to request APAC cluster for EU-only bank
        with self.assertRaises(PermissionError) as ctx:
            # Temporarily disable EU clusters to test strict enforcement
            self.router.clusters["sfu-eu-de-1"].is_active = False
            self.router.clusters["sfu-eu-ie-1"].is_active = False
            self.router.select_optimal_cluster("org_deutsche_bank")
        self.assertIn("Data Sovereignty Violation", str(ctx.exception))

    def test_cross_border_transfer_validation(self):
        # EU to EU -> Allowed
        allowed, reason = self.router.validate_cross_border_transfer(
            "org_deutsche_bank",
            SovereignRegion.EU_WEST,
            SovereignRegion.EU_WEST
        )
        self.assertTrue(allowed)

        # EU to US without E2EE -> Blocked for Deutsche Bank
        blocked, reason = self.router.validate_cross_border_transfer(
            "org_deutsche_bank",
            SovereignRegion.EU_WEST,
            SovereignRegion.US_EAST,
            is_e2ee=False
        )
        self.assertFalse(blocked)
        self.assertIn("E2EE encryption is required", reason)

        # EU to US with E2EE -> Strictly enforced bank policy still blocks foreign destination
        blocked_strict, _ = self.router.validate_cross_border_transfer(
            "org_deutsche_bank",
            SovereignRegion.EU_WEST,
            SovereignRegion.US_EAST,
            is_e2ee=True
        )
        self.assertFalse(blocked_strict)

        # Global Corp allowing US and EU -> Authorized
        allowed_global, _ = self.router.validate_cross_border_transfer(
            "org_global_corp",
            SovereignRegion.US_EAST,
            SovereignRegion.EU_WEST
        )
        self.assertTrue(allowed_global)

    def test_sanitize_metadata_for_transit(self):
        raw_meta = {
            "ip_address": "194.12.45.189",
            "email": "johann.schmidt@db.com",
            "mac_address": "00:1B:44:11:3A:B7",
            "device_serial": "SN-987654321",
            "session_id": "sess_eu_101",
            "bitrate_kbps": 2500
        }

        sanitized = self.router.sanitize_metadata_for_transit(raw_meta, "org_deutsche_bank")
        self.assertEqual(sanitized["ip_address"], "194.12.45.0/24")
        self.assertEqual(sanitized["email"], "j***@db.com")
        self.assertEqual(sanitized["mac_address"], "[REDACTED_BY_SOVEREIGNTY_POLICY]")
        self.assertEqual(sanitized["device_serial"], "[REDACTED_BY_SOVEREIGNTY_POLICY]")
        self.assertEqual(sanitized["session_id"], "sess_eu_101")
        self.assertEqual(sanitized["bitrate_kbps"], 2500)


if __name__ == "__main__":
    unittest.main()
