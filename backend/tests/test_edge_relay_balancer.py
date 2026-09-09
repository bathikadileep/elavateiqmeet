"""
Tests for High-Availability SFU Edge Relay & Geo-Proximity Load Balancer
========================================================================
Validates Haversine geodesic calculations, multi-factor node scoring,
inter-continental cascade bridging, and heartbeat failover.
"""

import time
import unittest
from backend.services.media.edge_relay_balancer import (
    EdgeRelayBalancer,
    GeoCoordinates,
    GeoProximityMath,
    NodeStatus,
)


class TestEdgeRelayBalancer(unittest.TestCase):

    def setUp(self):
        self.balancer = EdgeRelayBalancer()

        # Register global edge nodes:
        # US-East: North Virginia (38.9, -77.0)
        self.node_us_east = self.balancer.register_node(
            node_id="sfu-iad-01",
            region="us-east-1",
            datacenter="IAD",
            public_ip="198.51.100.10",
            signaling_url="wss://iad.elevateiq.meet",
            latitude=38.9,
            longitude=-77.0,
            max_capacity=500,
        )

        # US-West: Oregon (45.5, -122.6)
        self.node_us_west = self.balancer.register_node(
            node_id="sfu-pdx-01",
            region="us-west-2",
            datacenter="PDX",
            public_ip="198.51.100.20",
            signaling_url="wss://pdx.elevateiq.meet",
            latitude=45.5,
            longitude=-122.6,
            max_capacity=500,
        )

        # EU-Central: Frankfurt (50.1, 8.6)
        self.node_eu_central = self.balancer.register_node(
            node_id="sfu-fra-01",
            region="eu-central-1",
            datacenter="FRA",
            public_ip="198.51.100.30",
            signaling_url="wss://fra.elevateiq.meet",
            latitude=50.1,
            longitude=8.6,
            max_capacity=500,
        )

    def test_haversine_distance_calculation(self):
        # NYC (40.71, -74.00) to London (51.50, -0.12) ~ 5570 km
        nyc = GeoCoordinates(40.71, -74.00)
        london = GeoCoordinates(51.50, -0.12)
        dist = GeoProximityMath.calculate_distance_km(nyc, london)
        self.assertAlmostEqual(dist, 5570, delta=100)

    def test_geo_affinity_routing(self):
        # Participant in Seattle, WA (47.6, -122.3) -> should route to US-West (PDX)
        assignment_us = self.balancer.assign_optimal_node(
            peer_id="peer_seattle",
            room_code="room_geo_1",
            client_lat=47.6,
            client_lon=-122.3,
        )
        self.assertEqual(assignment_us.assigned_node_id, "sfu-pdx-01")
        self.assertEqual(assignment_us.region, "us-west-2")

        # Participant in Berlin, Germany (52.5, 13.4) -> should route to EU-Central (FRA)
        assignment_eu = self.balancer.assign_optimal_node(
            peer_id="peer_berlin",
            room_code="room_geo_2",
            client_lat=52.5,
            client_lon=13.4,
        )
        self.assertEqual(assignment_eu.assigned_node_id, "sfu-fra-01")
        self.assertEqual(assignment_eu.region, "eu-central-1")

    def test_inter_continental_cascade_bridging(self):
        # Participant 1 in New York joins Room A -> assigned to US-East
        p1 = self.balancer.assign_optimal_node(
            peer_id="p1_ny",
            room_code="room_cross_atlantic",
            client_lat=40.7,
            client_lon=-74.0,
        )
        self.assertEqual(p1.assigned_node_id, "sfu-iad-01")
        self.assertFalse(p1.is_cascade_bridged)

        # Participant 2 in Paris (48.8, 2.3) joins same Room A -> assigned to EU-Central with cascade bridge!
        p2 = self.balancer.assign_optimal_node(
            peer_id="p2_paris",
            room_code="room_cross_atlantic",
            client_lat=48.8,
            client_lon=2.3,
        )
        self.assertEqual(p2.assigned_node_id, "sfu-fra-01")
        self.assertTrue(p2.is_cascade_bridged)
        self.assertIsNotNone(p2.bridge_id)

    def test_cpu_headroom_avoids_overloaded_node(self):
        # Artificially overload US-West with 95% CPU
        self.balancer.record_heartbeat("sfu-pdx-01", active_streams=450, cpu_pct=95.0, status=NodeStatus.DEGRADED)

        # Client in California: although closest geographically to US-West,
        # the high load penalty should steer traffic to US-East if available!
        assignment = self.balancer.assign_optimal_node(
            peer_id="peer_cali",
            room_code="room_failover_1",
            client_lat=37.7,
            client_lon=-122.4,
        )
        self.assertNotEqual(assignment.assigned_node_id, "sfu-pdx-01")

    def test_heartbeat_timeout_marks_node_offline(self):
        # Fake outdated heartbeat on EU node (45s ago)
        self.node_eu_central.last_heartbeat_ts = time.time() - 45.0
        offline = self.balancer.purge_unhealthy_nodes()

        self.assertIn("sfu-fra-01", offline)
        self.assertEqual(self.node_eu_central.status, NodeStatus.OFFLINE)
        self.assertFalse(self.node_eu_central.is_available)


if __name__ == "__main__":
    unittest.main()
