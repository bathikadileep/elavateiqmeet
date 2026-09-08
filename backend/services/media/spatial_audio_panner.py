"""
Spatial Audio Panner Service
============================
HRTF-based 3D spatial audio positioning for multi-participant meetings.
Computes per-participant azimuth, elevation, distance gain, and ITD/ILD cues.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class RoomShape(str, Enum):
    CIRCLE = "circle"
    SEMICIRCLE = "semicircle"
    GRID = "grid"
    CUSTOM = "custom"


class DistanceModel(str, Enum):
    LINEAR = "linear"
    INVERSE = "inverse"
    EXPONENTIAL = "exponential"


@dataclass
class SpatialPosition:
    """3D Cartesian position in virtual audio space."""
    x: float = 0.0   # Left-Right  (-1.0 = hard left, +1.0 = hard right)
    y: float = 0.0   # Front-Back  (-1.0 = behind, +1.0 = front)
    z: float = 0.0   # Up-Down     (-1.0 = below, +1.0 = above)

    def to_spherical(self) -> Tuple[float, float, float]:
        """Convert to (azimuth_deg, elevation_deg, distance)."""
        distance = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if distance == 0:
            return 0.0, 0.0, 0.0
        azimuth = math.degrees(math.atan2(self.x, self.y))
        elevation = math.degrees(math.asin(self.z / distance))
        return azimuth, elevation, distance

    def distance_to(self, other: "SpatialPosition") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx**2 + dy**2 + dz**2)


@dataclass
class ParticipantAudioNode:
    participant_id: str
    display_name: str
    position: SpatialPosition = field(default_factory=SpatialPosition)
    gain_db: float = 0.0
    muted: bool = False
    is_speaking: bool = False
    pan_locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        az, el, dist = self.position.to_spherical()
        return {
            "participant_id": self.participant_id,
            "display_name": self.display_name,
            "position": {"x": self.position.x, "y": self.position.y, "z": self.position.z},
            "azimuth_deg": round(az, 2),
            "elevation_deg": round(el, 2),
            "distance": round(dist, 4),
            "gain_db": round(self.gain_db, 2),
            "muted": self.muted,
            "is_speaking": self.is_speaking,
            "pan_locked": self.pan_locked,
        }


@dataclass
class HRTFConfig:
    """Head-Related Transfer Function parameters."""
    head_radius_cm: float = 8.75       # Average adult head radius
    ear_distance_cm: float = 17.5      # Inter-aural distance
    speed_of_sound_cms: float = 34300  # cm/s at 20°C
    pinna_notch_hz: float = 8000.0     # Pinna notch frequency for elevation
    reference_distance_m: float = 1.0  # Reference distance for 0 dB gain

    @property
    def max_itd_ms(self) -> float:
        """Maximum inter-aural time difference in milliseconds."""
        return (self.ear_distance_cm / self.speed_of_sound_cms) * 1000.0


class SpatialAudioPanner:
    """
    Manages virtual 3D audio positioning for all meeting participants.
    Computes HRTF cues: azimuth, elevation, ITD, ILD, and distance gain.
    """

    _HEAD_SHADOW_DB_PER_RAD = 6.0   # Simplified ILD model
    _DISTANCE_REF_M = 1.0

    def __init__(
        self,
        room_shape: RoomShape = RoomShape.CIRCLE,
        distance_model: DistanceModel = DistanceModel.INVERSE,
        hrtf_config: Optional[HRTFConfig] = None,
        listener_position: Optional[SpatialPosition] = None,
    ) -> None:
        self.room_shape = room_shape
        self.distance_model = distance_model
        self.hrtf = hrtf_config or HRTFConfig()
        self.listener = listener_position or SpatialPosition(0.0, 0.0, 0.0)
        self._nodes: Dict[str, ParticipantAudioNode] = {}

    # ------------------------------------------------------------------
    # Participant management
    # ------------------------------------------------------------------

    def add_participant(
        self,
        participant_id: str,
        display_name: str,
        position: Optional[SpatialPosition] = None,
    ) -> ParticipantAudioNode:
        node = ParticipantAudioNode(
            participant_id=participant_id,
            display_name=display_name,
            position=position or SpatialPosition(),
        )
        self._nodes[participant_id] = node
        return node

    def remove_participant(self, participant_id: str) -> None:
        self._nodes.pop(participant_id, None)

    def get_participant(self, participant_id: str) -> Optional[ParticipantAudioNode]:
        return self._nodes.get(participant_id)

    def list_participants(self) -> List[ParticipantAudioNode]:
        return list(self._nodes.values())

    # ------------------------------------------------------------------
    # Layout algorithms
    # ------------------------------------------------------------------

    def auto_layout(self) -> Dict[str, SpatialPosition]:
        """Automatically arrange participants in the configured room shape."""
        participants = list(self._nodes.values())
        n = len(participants)
        positions: Dict[str, SpatialPosition] = {}

        if n == 0:
            return positions

        if self.room_shape == RoomShape.CIRCLE:
            positions = self._layout_circle(participants)
        elif self.room_shape == RoomShape.SEMICIRCLE:
            positions = self._layout_semicircle(participants)
        elif self.room_shape == RoomShape.GRID:
            positions = self._layout_grid(participants)
        else:
            positions = self._layout_circle(participants)

        for pid, pos in positions.items():
            self._nodes[pid].position = pos
        return positions

    def _layout_circle(
        self, participants: List[ParticipantAudioNode], radius: float = 1.0
    ) -> Dict[str, SpatialPosition]:
        n = len(participants)
        positions = {}
        for i, p in enumerate(participants):
            angle = (2 * math.pi * i) / n
            positions[p.participant_id] = SpatialPosition(
                x=radius * math.sin(angle),
                y=radius * math.cos(angle),
                z=0.0,
            )
        return positions

    def _layout_semicircle(
        self, participants: List[ParticipantAudioNode], radius: float = 1.0
    ) -> Dict[str, SpatialPosition]:
        n = len(participants)
        positions = {}
        for i, p in enumerate(participants):
            angle = math.pi * i / max(n - 1, 1)
            positions[p.participant_id] = SpatialPosition(
                x=radius * math.sin(angle) - radius / 2,
                y=radius * math.cos(angle),
                z=0.0,
            )
        return positions

    def _layout_grid(
        self, participants: List[ParticipantAudioNode]
    ) -> Dict[str, SpatialPosition]:
        n = len(participants)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        positions = {}
        for idx, p in enumerate(participants):
            row = idx // cols
            col = idx % cols
            positions[p.participant_id] = SpatialPosition(
                x=(col - cols / 2.0) * 0.4,
                y=(rows / 2.0 - row) * 0.4,
                z=0.0,
            )
        return positions

    # ------------------------------------------------------------------
    # HRTF computation
    # ------------------------------------------------------------------

    def compute_hrtf_cues(self, participant_id: str) -> Dict[str, float]:
        """Compute HRTF spatial cues for a given participant."""
        node = self._nodes.get(participant_id)
        if node is None:
            return {}

        azimuth, elevation, distance = node.position.to_spherical()
        az_rad = math.radians(azimuth)

        itd_ms = self._compute_itd(az_rad)
        ild_db = self._compute_ild(az_rad)
        gain_db = self._compute_distance_gain(distance)
        pinna_db = self._compute_pinna_notch(elevation)

        return {
            "azimuth_deg": round(azimuth, 2),
            "elevation_deg": round(elevation, 2),
            "distance_m": round(distance, 4),
            "itd_ms": round(itd_ms, 4),
            "ild_db": round(ild_db, 2),
            "gain_db": round(gain_db, 2),
            "pinna_notch_db": round(pinna_db, 2),
            "total_gain_db": round(gain_db + pinna_db, 2),
        }

    def compute_all_hrtf_cues(self) -> Dict[str, Dict[str, float]]:
        return {pid: self.compute_hrtf_cues(pid) for pid in self._nodes}

    def _compute_itd(self, azimuth_rad: float) -> float:
        """Woodworth formula for inter-aural time difference."""
        r = self.hrtf.head_radius_cm / self.hrtf.speed_of_sound_cms
        if abs(azimuth_rad) <= math.pi / 2:
            itd_s = r * (azimuth_rad + math.sin(azimuth_rad))
        else:
            itd_s = r * (math.copysign(math.pi, azimuth_rad) - azimuth_rad + math.sin(azimuth_rad))
        return itd_s * 1000.0  # Convert to ms

    def _compute_ild(self, azimuth_rad: float) -> float:
        """Simplified frequency-averaged ILD."""
        return self._HEAD_SHADOW_DB_PER_RAD * abs(azimuth_rad)

    def _compute_distance_gain(self, distance: float) -> float:
        """Compute gain attenuation by distance."""
        if distance <= 0:
            return 0.0
        ref = self.hrtf.reference_distance_m
        if self.distance_model == DistanceModel.LINEAR:
            gain = max(0.0, 1.0 - distance / (ref * 10))
            return 20 * math.log10(max(gain, 1e-6))
        elif self.distance_model == DistanceModel.INVERSE:
            return -20 * math.log10(max(distance / ref, 1.0))
        elif self.distance_model == DistanceModel.EXPONENTIAL:
            return -20 * (distance / ref) * math.log10(2)
        return 0.0

    def _compute_pinna_notch(self, elevation_deg: float) -> float:
        """Simplified pinna elevation cue (dB)."""
        # Higher elevations add a slight notch / coloration
        el_rad = math.radians(abs(elevation_deg))
        return -2.0 * math.sin(el_rad)

    # ------------------------------------------------------------------
    # Speaking detection helpers
    # ------------------------------------------------------------------

    def set_speaking(self, participant_id: str, is_speaking: bool) -> None:
        if participant_id in self._nodes:
            self._nodes[participant_id].is_speaking = is_speaking

    def get_active_speakers(self) -> List[str]:
        return [pid for pid, n in self._nodes.items() if n.is_speaking]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def get_scene(self) -> Dict[str, Any]:
        return {
            "room_shape": self.room_shape.value,
            "distance_model": self.distance_model.value,
            "listener": {"x": self.listener.x, "y": self.listener.y, "z": self.listener.z},
            "hrtf": {
                "head_radius_cm": self.hrtf.head_radius_cm,
                "max_itd_ms": round(self.hrtf.max_itd_ms, 4),
            },
            "participants": [n.to_dict() for n in self._nodes.values()],
            "hrtf_cues": self.compute_all_hrtf_cues(),
        }

    def apply_scene(self, scene: Dict[str, Any]) -> None:
        """Restore panner state from a previously serialized scene dict."""
        for p_data in scene.get("participants", []):
            pos_data = p_data.get("position", {})
            pos = SpatialPosition(
                x=pos_data.get("x", 0.0),
                y=pos_data.get("y", 0.0),
                z=pos_data.get("z", 0.0),
            )
            node = ParticipantAudioNode(
                participant_id=p_data["participant_id"],
                display_name=p_data.get("display_name", "Unknown"),
                position=pos,
                gain_db=p_data.get("gain_db", 0.0),
                muted=p_data.get("muted", False),
                is_speaking=p_data.get("is_speaking", False),
            )
            self._nodes[node.participant_id] = node
