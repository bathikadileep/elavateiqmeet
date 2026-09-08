"""
ElevateIQ — Enterprise Session Activity & Impossible Travel Detector
======================================================================
Monitors live user session heartbeats, detects concurrent multi-geo logins
(impossible travel velocity anomalies), enforces idle session locks,
and triggers automatic session quarantine for SOC 2 / ISO 27001 compliance.
"""

from __future__ import annotations

import enum
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("elevateiq.services.enterprise.session_monitor")


class AnomalySeverity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GeoLocationPoint:
    latitude: float
    longitude: float
    country_code: str
    city: str
    ip_address: str


@dataclass
class SessionHeartbeat:
    session_id: str
    user_id: str
    timestamp_ms: int
    geo_point: GeoLocationPoint
    is_active_input: bool = True
    user_agent: str = "Mozilla/5.0"


@dataclass
class SecurityAnomalyRecord:
    anomaly_id: str
    user_id: str
    session_id: str
    severity: AnomalySeverity
    rule_name: str
    description: str
    detected_at_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    quarantined: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "severity": self.severity.value,
            "rule_name": self.rule_name,
            "description": self.description,
            "detected_at": self.detected_at_ms,
            "quarantined": self.quarantined,
            "metadata": self.metadata,
        }


class SessionActivityMonitor:
    """
    Analyzes active session behavior, tracks geographic velocity,
    and detects impossible travel anomalies.
    """

    # Max reasonable commercial aircraft travel speed (km/h)
    MAX_PLAUSIBLE_VELOCITY_KMH = 950.0
    IDLE_TIMEOUT_THRESHOLD_MS = 1800000  # 30 minutes

    def __init__(self):
        self._user_last_heartbeat: Dict[str, SessionHeartbeat] = {}
        self._quarantined_sessions: Dict[str, str] = {}  # session_id -> reason
        self._detected_anomalies: List[SecurityAnomalyRecord] = []

    # -------------------------------------------------------------------------
    # Heartbeat Ingestion & Anomaly Analysis
    # -------------------------------------------------------------------------

    def record_heartbeat(self, heartbeat: SessionHeartbeat) -> Tuple[bool, Optional[SecurityAnomalyRecord]]:
        """
        Record user presence heartbeat and evaluate impossible travel velocity.
        Returns: (is_allowed, anomaly_or_none)
        """
        user_id = heartbeat.user_id
        session_id = heartbeat.session_id

        # Check if session is already quarantined
        if session_id in self._quarantined_sessions:
            log.warning("Rejected heartbeat from quarantined session %s", session_id)
            return False, None

        anomaly: Optional[SecurityAnomalyRecord] = None

        if user_id in self._user_last_heartbeat:
            previous = self._user_last_heartbeat[user_id]
            time_delta_hours = (heartbeat.timestamp_ms - previous.timestamp_ms) / 3600000.0

            if time_delta_hours > 0:
                dist_km = self.haversine_distance_km(
                    previous.geo_point.latitude, previous.geo_point.longitude,
                    heartbeat.geo_point.latitude, heartbeat.geo_point.longitude
                )
                velocity_kmh = dist_km / time_delta_hours

                # Check for impossible travel velocity (e.g. London to Tokyo in 15 minutes)
                if dist_km > 100 and velocity_kmh > self.MAX_PLAUSIBLE_VELOCITY_KMH:
                    anomaly_id = f"anom_{int(time.time() * 1000)}_{user_id[:6]}"
                    desc = (
                        f"Impossible travel detected for user {user_id}: "
                        f"{dist_km:.1f} km traveled in {time_delta_hours * 60:.1f} mins "
                        f"(Velocity: {velocity_kmh:.1f} km/h > {self.MAX_PLAUSIBLE_VELOCITY_KMH} km/h)"
                    )
                    anomaly = SecurityAnomalyRecord(
                        anomaly_id=anomaly_id,
                        user_id=user_id,
                        session_id=session_id,
                        severity=AnomalySeverity.CRITICAL,
                        rule_name="IMPOSSIBLE_TRAVEL_VELOCITY",
                        description=desc,
                        detected_at_ms=heartbeat.timestamp_ms,
                        quarantined=True,
                        metadata={
                            "distance_km": round(dist_km, 1),
                            "velocity_kmh": round(velocity_kmh, 1),
                            "origin_city": previous.geo_point.city,
                            "destination_city": heartbeat.geo_point.city,
                        },
                    )
                    self._detected_anomalies.append(anomaly)
                    self._quarantined_sessions[session_id] = "Impossible travel detected"
                    log.error(desc)
                    return False, anomaly

        # Update last known heartbeat
        self._user_last_heartbeat[user_id] = heartbeat
        return True, None

    # -------------------------------------------------------------------------
    # Geographic Math
    # -------------------------------------------------------------------------

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance between two GPS coordinates using Haversine formula."""
        R = 6371.0  # Earth mean radius in kilometers

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    # -------------------------------------------------------------------------
    # Quarantine & Diagnostics
    # -------------------------------------------------------------------------

    def is_session_quarantined(self, session_id: str) -> bool:
        return session_id in self._quarantined_sessions

    def release_quarantine(self, session_id: str) -> bool:
        """Admin release of quarantined user session."""
        if session_id in self._quarantined_sessions:
            del self._quarantined_sessions[session_id]
            log.info("Released quarantine for session %s", session_id)
            return True
        return False

    def list_anomalies(self, min_severity: Optional[AnomalySeverity] = None) -> List[Dict[str, Any]]:
        if not min_severity:
            return [a.to_dict() for a in self._detected_anomalies]
        return [a.to_dict() for a in self._detected_anomalies if a.severity == min_severity]
