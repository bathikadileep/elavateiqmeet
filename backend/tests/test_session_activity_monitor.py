"""
ElevateIQ — Unit Test Suite for Session Activity & Impossible Travel Detector
=============================================================================
Tests heartbeat ingestion, Haversine distance calculations, impossible travel
anomaly triggering, automatic session quarantine, and administrative release.
"""

import unittest
from backend.services.enterprise.session_activity_monitor import (
    SessionActivityMonitor,
    SessionHeartbeat,
    GeoLocationPoint,
    AnomalySeverity,
)


class SessionActivityMonitorTestSuite(unittest.TestCase):

    def setUp(self):
        self.monitor = SessionActivityMonitor()

        # San Francisco coordinates
        self.sf_geo = GeoLocationPoint(
            latitude=37.7749,
            longitude=-122.4194,
            country_code="US",
            city="San Francisco",
            ip_address="198.51.100.1",
        )

        # London coordinates (~8,600 km away)
        self.london_geo = GeoLocationPoint(
            latitude=51.5074,
            longitude=-0.1278,
            country_code="GB",
            city="London",
            ip_address="203.0.113.5",
        )

        # San Jose coordinates (~75 km away)
        self.sj_geo = GeoLocationPoint(
            latitude=37.3382,
            longitude=-121.8863,
            country_code="US",
            city="San Jose",
            ip_address="198.51.100.55",
        )

    def test_haversine_distance_calculation(self):
        """Verify distance between SF and London is ~8,600 km."""
        dist = SessionActivityMonitor.haversine_distance_km(
            self.sf_geo.latitude, self.sf_geo.longitude,
            self.london_geo.latitude, self.london_geo.longitude,
        )
        self.assertGreater(dist, 8500)
        self.assertLess(dist, 8750)

    def test_normal_stationary_heartbeat_allowed(self):
        """Verify sequential heartbeats from the same location are allowed."""
        h1 = SessionHeartbeat("sess_1", "usr_alice", 1000000, self.sf_geo)
        h2 = SessionHeartbeat("sess_1", "usr_alice", 1060000, self.sf_geo)  # 1 min later

        ok1, anom1 = self.monitor.record_heartbeat(h1)
        ok2, anom2 = self.monitor.record_heartbeat(h2)

        self.assertTrue(ok1)
        self.assertIsNone(anom1)
        self.assertTrue(ok2)
        self.assertIsNone(anom2)

    def test_plausible_travel_allowed(self):
        """SF to San Jose (75 km) in 1.5 hours = 50 km/h (plausible driving)."""
        t1 = 1000000
        t2 = t1 + int(1.5 * 3600 * 1000)  # 1.5 hours later

        h1 = SessionHeartbeat("sess_2", "usr_bob", t1, self.sf_geo)
        h2 = SessionHeartbeat("sess_2", "usr_bob", t2, self.sj_geo)

        ok1, _ = self.monitor.record_heartbeat(h1)
        ok2, anom2 = self.monitor.record_heartbeat(h2)

        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertIsNone(anom2)

    def test_impossible_travel_detected_and_quarantined(self):
        """SF to London (8,600 km) in 10 minutes = 51,600 km/h (impossible travel!)."""
        t1 = 1000000
        t2 = t1 + (10 * 60 * 1000)  # 10 minutes later

        h1 = SessionHeartbeat("sess_3", "usr_carol", t1, self.sf_geo)
        h2 = SessionHeartbeat("sess_compromised", "usr_carol", t2, self.london_geo)

        ok1, anom1 = self.monitor.record_heartbeat(h1)
        ok2, anom2 = self.monitor.record_heartbeat(h2)

        self.assertTrue(ok1)
        self.assertFalse(ok2)  # Blocked!
        self.assertIsNotNone(anom2)
        self.assertEqual(anom2.severity, AnomalySeverity.CRITICAL)
        self.assertEqual(anom2.rule_name, "IMPOSSIBLE_TRAVEL_VELOCITY")
        self.assertTrue(anom2.quarantined)

        # Subsequent requests from compromised session are rejected
        h3 = SessionHeartbeat("sess_compromised", "usr_carol", t2 + 1000, self.london_geo)
        ok3, _ = self.monitor.record_heartbeat(h3)
        self.assertFalse(ok3)

    def test_release_quarantine(self):
        """Test admin releasing quarantined session."""
        self.monitor._quarantined_sessions["sess_locked"] = "Manual lock"
        self.assertTrue(self.monitor.is_session_quarantined("sess_locked"))

        released = self.monitor.release_quarantine("sess_locked")
        self.assertTrue(released)
        self.assertFalse(self.monitor.is_session_quarantined("sess_locked"))

    def test_list_anomalies_filtered(self):
        """Test querying anomalies with severity filter."""
        t1 = 1000000
        t2 = t1 + 60000  # 1 minute later
        self.monitor.record_heartbeat(SessionHeartbeat("s1", "u1", t1, self.sf_geo))
        self.monitor.record_heartbeat(SessionHeartbeat("s2", "u1", t2, self.london_geo))

        all_anoms = self.monitor.list_anomalies()
        self.assertEqual(len(all_anoms), 1)

        crit_anoms = self.monitor.list_anomalies(min_severity=AnomalySeverity.CRITICAL)
        self.assertEqual(len(crit_anoms), 1)


if __name__ == "__main__":
    unittest.main()
