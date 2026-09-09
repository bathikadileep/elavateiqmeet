"""
High-Availability SFU Edge Relay & Geo-Proximity Load Balancer
==============================================================
Manages globally distributed Selective Forwarding Unit (SFU) media nodes.
Computes geo-affinity, network latency profiles, and cluster headroom to route
participants to the nearest optimal media edge while establishing inter-region
relay cascade bridges.

Features:
- Great-Circle Haversine geodesic distance calculation.
- Multi-factor routing score (Geo Proximity, Measured RTT, and CPU/Bandwidth Headroom).
- Automatic inter-continental cascade bridging to minimize cross-oceanic jitter.
- Dynamic health-check heartbeats with automated failover and drain evacuation.
- Real-time routing decisions and topology telemetry.
"""

from __future__ import annotations

import enum
import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("elevateiq.services.media.edge_balancer")


class NodeStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DRAINING = "DRAINING"
    OFFLINE = "OFFLINE"


@dataclass
class GeoCoordinates:
    """Geographic latitude and longitude."""
    latitude: float
    longitude: float


@dataclass
class SfuEdgeNode:
    """Represents an edge media server node in a global cluster."""
    node_id: str
    region: str
    datacenter: str
    public_ip: str
    signaling_url: str
    geo: GeoCoordinates
    max_streams_capacity: int = 1000
    active_streams_count: int = 0
    cpu_utilization_pct: float = 0.0
    status: NodeStatus = NodeStatus.HEALTHY
    last_heartbeat_ts: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def utilization_ratio(self) -> float:
        if self.max_streams_capacity <= 0:
            return 1.0
        return min(1.0, self.active_streams_count / self.max_streams_capacity)

    @property
    def is_available(self) -> bool:
        return self.status in (NodeStatus.HEALTHY, NodeStatus.DEGRADED) and self.utilization_ratio < 0.95


@dataclass
class CascadeBridge:
    """Inter-region relay link connecting two edge nodes for cross-region meetings."""
    bridge_id: str
    room_code: str
    source_node_id: str
    target_node_id: str
    forwarded_tracks_count: int = 0
    established_at: float = field(default_factory=time.time)
    last_active_ts: float = field(default_factory=time.time)


@dataclass
class EdgeRoutingAssignment:
    """Routing assignment result for a meeting participant."""
    peer_id: str
    room_code: str
    assigned_node_id: str
    assigned_node_url: str
    region: str
    estimated_rtt_ms: float
    distance_km: float
    is_cascade_bridged: bool = False
    bridge_id: Optional[str] = None
    backup_node_id: Optional[str] = None


class GeoProximityMath:
    """Computes geodesic surface distances using Haversine formula."""

    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def calculate_distance_km(cls, p1: GeoCoordinates, p2: GeoCoordinates) -> float:
        lat1_rad = math.radians(p1.latitude)
        lat2_rad = math.radians(p2.latitude)
        dlat_rad = math.radians(p2.latitude - p1.latitude)
        dlon_rad = math.radians(p2.longitude - p1.longitude)

        a = (
            math.sin(dlat_rad / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return cls.EARTH_RADIUS_KM * c

    @classmethod
    def estimate_fiber_rtt_ms(cls, distance_km: float) -> float:
        """
        Estimates baseline round-trip fiber optic latency:
        Speed of light in glass ~ 200 km/ms. RTT = 2 * (dist / 200) * 1.4 (routing overhead factor).
        """
        if distance_km <= 0:
            return 2.0
        return max(5.0, round((distance_km / 100.0) * 1.4, 1))


class EdgeRelayBalancer:
    """
    Global SFU edge cluster load balancer and inter-region cascade manager.
    """

    HEARTBEAT_TIMEOUT_SEC = 30.0

    def __init__(self) -> None:
        self.nodes: Dict[str, SfuEdgeNode] = {}  # node_id -> SfuEdgeNode
        self.room_assignments: Dict[str, Set[str]] = {}  # room_code -> set of assigned node_ids
        self.peer_assignments: Dict[str, EdgeRoutingAssignment] = {}  # peer_id -> Assignment
        self.bridges: Dict[str, CascadeBridge] = {}  # bridge_id -> CascadeBridge

    # -------------------------------------------------------------------------
    # Node Cluster Registration & Health Heartbeats
    # -------------------------------------------------------------------------
    def register_node(
        self,
        node_id: str,
        region: str,
        datacenter: str,
        public_ip: str,
        signaling_url: str,
        latitude: float,
        longitude: float,
        max_capacity: int = 1000,
    ) -> SfuEdgeNode:
        """Registers a new SFU media server edge node."""
        node = SfuEdgeNode(
            node_id=node_id,
            region=region,
            datacenter=datacenter,
            public_ip=public_ip,
            signaling_url=signaling_url,
            geo=GeoCoordinates(latitude, longitude),
            max_streams_capacity=max_capacity,
        )
        self.nodes[node_id] = node
        logger.info("Registered SFU edge node: %s (%s, %s)", node_id, region, datacenter)
        return node

    def record_heartbeat(
        self,
        node_id: str,
        active_streams: int,
        cpu_pct: float,
        status: Optional[NodeStatus] = None,
    ) -> bool:
        """Records telemetry heartbeat from an edge node."""
        node = self.nodes.get(node_id)
        if not node:
            return False

        node.active_streams_count = active_streams
        node.cpu_utilization_pct = cpu_pct
        node.last_heartbeat_ts = time.time()

        if status:
            node.status = status
        elif cpu_pct >= 90.0:
            node.status = NodeStatus.DEGRADED
        else:
            node.status = NodeStatus.HEALTHY

        return True

    def purge_unhealthy_nodes(self) -> List[str]:
        """Marks nodes missing heartbeats as OFFLINE."""
        now = time.time()
        offline_nodes: List[str] = []
        for node in self.nodes.values():
            if node.status != NodeStatus.OFFLINE:
                if (now - node.last_heartbeat_ts) > self.HEARTBEAT_TIMEOUT_SEC:
                    node.status = NodeStatus.OFFLINE
                    offline_nodes.append(node.node_id)
                    logger.warning("SFU Node %s marked OFFLINE due to heartbeat timeout", node.node_id)
        return offline_nodes

    # -------------------------------------------------------------------------
    # Intelligent Geo-Affinity Routing
    # -------------------------------------------------------------------------
    def assign_optimal_node(
        self,
        peer_id: str,
        room_code: str,
        client_lat: float,
        client_lon: float,
        measured_rtt_samples: Optional[Dict[str, float]] = None,
    ) -> EdgeRoutingAssignment:
        """
        Determines the optimal SFU edge node for a participant based on:
        1. Distance & estimated fiber RTT.
        2. Live client-reported RTT pings (if provided).
        3. Node load and capacity headroom.
        4. Affinity to already established nodes in the same meeting room.
        """
        self.purge_unhealthy_nodes()
        available_nodes = [n for n in self.nodes.values() if n.is_available]

        if not available_nodes:
            raise RuntimeError("No available healthy SFU edge nodes in cluster!")

        client_geo = GeoCoordinates(client_lat, client_lon)
        measured_rtt = measured_rtt_samples or {}

        # Existing nodes hosting this room
        existing_room_nodes = self.room_assignments.get(room_code, set())

        scored_nodes: List[Tuple[float, SfuEdgeNode, float, float]] = []  # (score, node, dist_km, rtt_ms)

        for node in available_nodes:
            dist_km = GeoProximityMath.calculate_distance_km(client_geo, node.geo)
            rtt_ms = measured_rtt.get(node.node_id, GeoProximityMath.estimate_fiber_rtt_ms(dist_km))

            # Proximity factor (0 to 1, higher is better)
            # 5000 km maps to ~0.5
            proximity_score = 1.0 / (1.0 + (dist_km / 1500.0))

            # Latency factor (0 to 1, lower RTT is better)
            latency_score = 1.0 / (1.0 + (rtt_ms / 50.0))

            # Headroom factor
            headroom_score = (1.0 - node.utilization_ratio) * (1.0 - (node.cpu_utilization_pct / 100.0))

            # Room affinity bonus (save inter-region bandwidth if proximity is close enough)
            affinity_bonus = 0.25 if node.node_id in existing_room_nodes else 0.0
            degradation_penalty = 0.35 if node.status == NodeStatus.DEGRADED else 0.0

            total_score = (
                (0.35 * proximity_score)
                + (0.30 * latency_score)
                + (0.35 * headroom_score)
                + affinity_bonus
                - degradation_penalty
            )

            scored_nodes.append((total_score, node, dist_km, rtt_ms))

        # Sort descending by score
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        best_score, best_node, best_dist, best_rtt = scored_nodes[0]
        backup_node = scored_nodes[1][1].node_id if len(scored_nodes) > 1 else None

        # Check cascade bridge requirement
        is_bridged = False
        bridge_id = None

        if existing_room_nodes and best_node.node_id not in existing_room_nodes:
            # Connect best_node with primary room node via cascade bridge
            primary_room_node = list(existing_room_nodes)[0]
            bridge = self._ensure_cascade_bridge(room_code, primary_room_node, best_node.node_id)
            is_bridged = True
            bridge_id = bridge.bridge_id

        # Update room assignments and node counter
        if room_code not in self.room_assignments:
            self.room_assignments[room_code] = set()
        self.room_assignments[room_code].add(best_node.node_id)
        best_node.active_streams_count += 1

        assignment = EdgeRoutingAssignment(
            peer_id=peer_id,
            room_code=room_code,
            assigned_node_id=best_node.node_id,
            assigned_node_url=best_node.signaling_url,
            region=best_node.region,
            estimated_rtt_ms=best_rtt,
            distance_km=round(best_dist, 1),
            is_cascade_bridged=is_bridged,
            bridge_id=bridge_id,
            backup_node_id=backup_node,
        )

        self.peer_assignments[peer_id] = assignment
        logger.info(
            "Assigned peer %s to edge %s (Region: %s, Dist: %.1f km, RTT: %.1f ms, Bridged: %s)",
            peer_id, best_node.node_id, best_node.region, best_dist, best_rtt, is_bridged
        )
        return assignment

    def release_peer(self, peer_id: str) -> None:
        """Frees peer assignment and decrements active stream counters."""
        assignment = self.peer_assignments.pop(peer_id, None)
        if not assignment:
            return

        node = self.nodes.get(assignment.assigned_node_id)
        if node and node.active_streams_count > 0:
            node.active_streams_count -= 1

    def _ensure_cascade_bridge(self, room_code: str, node_a: str, node_b: str) -> CascadeBridge:
        """Finds or instantiates an inter-region relay bridge for a room."""
        for b in self.bridges.values():
            if b.room_code == room_code:
                if (b.source_node_id == node_a and b.target_node_id == node_b) or (b.source_node_id == node_b and b.target_node_id == node_a):
                    b.last_active_ts = time.time()
                    return b

        bridge_id = f"bridge_{uuid.uuid4().hex[:12]}"
        bridge = CascadeBridge(
            bridge_id=bridge_id,
            room_code=room_code,
            source_node_id=node_a,
            target_node_id=node_b,
        )
        self.bridges[bridge_id] = bridge
        logger.info("Instantiated SFU cascade bridge %s between %s <-> %s for room %s", bridge_id, node_a, node_b, room_code)
        return bridge
