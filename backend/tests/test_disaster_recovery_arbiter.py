"""
Tests for Enterprise Disaster Recovery & Split-Brain Arbiter
============================================================
Validates multi-datacenter quorum lease tracking, automated failover detection,
fencing token monotonicity, and anti-split-brain write validation.
"""

import time
import unittest
from backend.services.enterprise.disaster_recovery_arbiter import (
    DisasterRecoveryArbiter,
    RegionRole,
    FailoverTriggerType,
)


class TestDisasterRecoveryArbiter(unittest.TestCase):

    def setUp(self):
        self.arbiter = DisasterRecoveryArbiter(tenant_id="tenant_global_finance")

        # Primary region (US-East)
        self.primary = self.arbiter.register_region(
            region_id="us-east-1",
            cluster_name="Primary DC (Ashburn)",
            endpoint_url="https://us-east.elevateiq.meet",
            role=RegionRole.PRIMARY,
        )

        # Hot Standby (EU-Central)
        self.secondary = self.arbiter.register_region(
            region_id="eu-central-1",
            cluster_name="Hot Standby (Frankfurt)",
            endpoint_url="https://eu-central.elevateiq.meet",
            role=RegionRole.SECONDARY_HOT_STANDBY,
        )

    def test_initial_state_and_lease(self):
        self.assertEqual(self.arbiter.current_primary_region, "us-east-1")
        self.assertTrue(self.arbiter.validate_write_lease("us-east-1", client_fencing_token=1))
        self.assertFalse(self.arbiter.validate_write_lease("eu-central-1", client_fencing_token=1))

    def test_evaluate_health_healthy_primary(self):
        self.arbiter.record_region_heartbeat("us-east-1", replication_lag_ms=0.0, is_healthy=True)
        needs_fo, candidate = self.arbiter.evaluate_cluster_health()
        self.assertFalse(needs_fo)
        self.assertIsNone(candidate)

    def test_automated_failover_on_primary_unhealthy(self):
        # Mark primary as unhealthy / dead
        self.primary.is_healthy = False
        self.arbiter.record_region_heartbeat("eu-central-1", replication_lag_ms=120.0, is_healthy=True)

        needs_fo, candidate = self.arbiter.evaluate_cluster_health()
        self.assertTrue(needs_fo)
        self.assertEqual(candidate, "eu-central-1")

        # Execute failover
        event = self.arbiter.execute_failover(
            target_region="eu-central-1",
            trigger_type=FailoverTriggerType.AUTOMATIC_HEALTH_CHECK,
            initiated_by="ClusterHealthMonitor",
            reason="Primary US-East health probe failure",
        )

        self.assertEqual(event.to_region, "eu-central-1")
        self.assertEqual(event.from_region, "us-east-1")
        self.assertEqual(self.arbiter.current_primary_region, "eu-central-1")
        self.assertEqual(self.primary.role, RegionRole.ISOLATED)
        self.assertEqual(self.secondary.role, RegionRole.PRIMARY)

        # Anti-split-brain verification:
        # Former primary writes with old token 1 MUST BE REJECTED!
        self.assertFalse(self.arbiter.validate_write_lease("us-east-1", client_fencing_token=1))
        # New primary with new token 2 MUST BE ACCEPTED!
        self.assertTrue(self.arbiter.validate_write_lease("eu-central-1", client_fencing_token=event.fencing_token))

    def test_manual_admin_failover(self):
        self.arbiter.record_region_heartbeat("eu-central-1", replication_lag_ms=45.0, is_healthy=True)

        event = self.arbiter.execute_failover(
            target_region="eu-central-1",
            trigger_type=FailoverTriggerType.MANUAL_ADMIN_OVERRIDE,
            initiated_by="DevOpsAdmin",
            reason="Planned maintenance in US datacenter",
        )

        self.assertEqual(self.arbiter.current_primary_region, "eu-central-1")
        self.assertEqual(event.trigger_type, FailoverTriggerType.MANUAL_ADMIN_OVERRIDE)
        self.assertEqual(len(self.arbiter.failover_history), 1)


if __name__ == "__main__":
    unittest.main()
