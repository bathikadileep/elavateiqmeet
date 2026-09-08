"""
ElevateIQ — Meeting Screen & Composite Recording Engine
========================================================
Orchestrates multi-track audio/video recording sessions for meeting rooms.
Mixes screen share streams and composite participant audio into segmented WebM/MP4
containers with pause/resume support, segment bookmarking, and cloud upload dispatch.
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("elevateiq.services.media.recording")


class RecordingState(str, enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoResolution(str, enum.Enum):
    SD_480P = "854x480"
    HD_720P = "1280x720"
    FULL_HD_1080P = "1920x1080"
    QUAD_HD_1440P = "2560x1440"


@dataclass
class RecordingBookmark:
    bookmark_id: str
    timestamp_offset_ms: int
    label: str
    created_by: str


@dataclass
class RecordingSegment:
    segment_index: int
    start_time_ms: int
    end_time_ms: int
    duration_ms: int
    file_path: str
    file_size_bytes: int
    sha256_checksum: str


@dataclass
class RecordingSession:
    recording_id: str
    room_code: str
    host_user_id: str
    state: RecordingState = RecordingState.IDLE
    resolution: VideoResolution = VideoResolution.HD_720P
    fps: int = 30
    bitrate_kbps: int = 2500
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None
    pause_time_ms: Optional[int] = None
    total_paused_duration_ms: int = 0
    segments: List[RecordingSegment] = field(default_factory=list)
    bookmarks: List[RecordingBookmark] = field(default_factory=list)
    output_directory: str = "/tmp/recordings"
    legal_hold_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration_ms(self) -> int:
        if not self.start_time_ms:
            return 0
        end = self.end_time_ms or int(time.time() * 1000)
        return max(0, (end - self.start_time_ms) - self.total_paused_duration_ms)

    @property
    def total_size_bytes(self) -> int:
        return sum(s.file_size_bytes for s in self.segments)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recording_id": self.recording_id,
            "room_code": self.room_code,
            "host_user_id": self.host_user_id,
            "state": self.state.value,
            "resolution": self.resolution.value,
            "fps": self.fps,
            "bitrate_kbps": self.bitrate_kbps,
            "duration_ms": self.total_duration_ms,
            "total_size_bytes": self.total_size_bytes,
            "segment_count": len(self.segments),
            "bookmarks": [
                {"id": b.bookmark_id, "offset_ms": b.timestamp_offset_ms, "label": b.label}
                for b in self.bookmarks
            ],
            "legal_hold": self.legal_hold_enabled,
        }


class ScreenRecorderEngine:
    """
    Manages active audio/video recording sessions for virtual rooms.
    Simulates muxing of audio/video frames into rolling segment files.
    """

    DEFAULT_SEGMENT_DURATION_MS = 600000  # 10 minutes rolling segments

    def __init__(self, base_storage_dir: str = "/var/elviq/recordings"):
        self.base_storage_dir = base_storage_dir
        self._sessions: Dict[str, RecordingSession] = {}

    def start_recording(
        self,
        room_code: str,
        host_user_id: str,
        resolution: VideoResolution = VideoResolution.HD_720P,
        fps: int = 30,
        bitrate_kbps: int = 2500
    ) -> RecordingSession:
        """Initialize and start recording for a room."""
        # Check if room already has active recording
        for s in self._sessions.values():
            if s.room_code == room_code and s.state in (RecordingState.RECORDING, RecordingState.PAUSED):
                log.warning("Room %s already has active recording session %s", room_code, s.recording_id)
                return s

        rec_id = f"rec_{hashlib.sha256(f'{room_code}:{host_user_id}:{time.time()}'.encode()).hexdigest()[:12]}"
        now = int(time.time() * 1000)

        session = RecordingSession(
            recording_id=rec_id,
            room_code=room_code,
            host_user_id=host_user_id,
            state=RecordingState.RECORDING,
            resolution=resolution,
            fps=fps,
            bitrate_kbps=bitrate_kbps,
            start_time_ms=now,
            output_directory=os.path.join(self.base_storage_dir, rec_id),
        )

        self._sessions[rec_id] = session
        log.info("Started recording session %s for room %s (Resolution: %s, %d fps)",
                 rec_id, room_code, resolution.value, fps)
        return session

    def pause_recording(self, recording_id: str) -> bool:
        """Temporarily pause video capture without closing session."""
        session = self._sessions.get(recording_id)
        if not session or session.state != RecordingState.RECORDING:
            return False

        session.state = RecordingState.PAUSED
        session.pause_time_ms = int(time.time() * 1000)
        log.info("Paused recording %s", recording_id)
        return True

    def resume_recording(self, recording_id: str) -> bool:
        """Resume paused capture."""
        session = self._sessions.get(recording_id)
        if not session or session.state != RecordingState.PAUSED or not session.pause_time_ms:
            return False

        now = int(time.time() * 1000)
        paused_delta = now - session.pause_time_ms
        session.total_paused_duration_ms += paused_delta
        session.pause_time_ms = None
        session.state = RecordingState.RECORDING
        log.info("Resumed recording %s (Paused duration was %d ms)", recording_id, paused_delta)
        return True

    def add_bookmark(self, recording_id: str, label: str, created_by: str) -> Optional[RecordingBookmark]:
        """Add a key timestamp marker to the recording for chapter navigation."""
        session = self._sessions.get(recording_id)
        if not session:
            return None

        offset = session.total_duration_ms
        bookmark = RecordingBookmark(
            bookmark_id=f"bm_{int(time.time() * 1000)}",
            timestamp_offset_ms=offset,
            label=label,
            created_by=created_by,
        )
        session.bookmarks.append(bookmark)
        log.info("Added bookmark '%s' at offset %d ms in recording %s", label, offset, recording_id)
        return bookmark

    def seal_segment(self, recording_id: str, approx_duration_ms: int = 60000) -> Optional[RecordingSegment]:
        """Complete a rolling recording segment chunk."""
        session = self._sessions.get(recording_id)
        if not session:
            return None

        seg_idx = len(session.segments) + 1
        now = int(time.time() * 1000)
        start_ts = now - approx_duration_ms
        file_path = os.path.join(session.output_directory, f"segment_{seg_idx:04d}.webm")
        # Approximate file size based on bitrate (bitrate_kbps * 1000 / 8 * seconds)
        size_bytes = int((session.bitrate_kbps * 1000 / 8) * (approx_duration_ms / 1000))
        checksum = hashlib.sha256(f"{recording_id}:{seg_idx}:{size_bytes}".encode()).hexdigest()

        segment = RecordingSegment(
            segment_index=seg_idx,
            start_time_ms=start_ts,
            end_time_ms=now,
            duration_ms=approx_duration_ms,
            file_path=file_path,
            file_size_bytes=size_bytes,
            sha256_checksum=checksum,
        )
        session.segments.append(segment)
        return segment

    def stop_recording(self, recording_id: str) -> Optional[RecordingSession]:
        """Finalize and stop recording session."""
        session = self._sessions.get(recording_id)
        if not session or session.state in (RecordingState.STOPPED, RecordingState.COMPLETED):
            return None

        # Seal any final segment
        self.seal_segment(recording_id, approx_duration_ms=30000)
        session.state = RecordingState.STOPPED
        session.end_time_ms = int(time.time() * 1000)
        log.info("Stopped recording session %s (Total Duration: %d ms, Segments: %d)",
                 recording_id, session.total_duration_ms, len(session.segments))
        return session

    def set_legal_hold(self, recording_id: str, enabled: bool) -> bool:
        """Lock recording from automatic lifecycle expiration/deletion."""
        session = self._sessions.get(recording_id)
        if not session:
            return False
        session.legal_hold_enabled = enabled
        log.info("Set legal hold = %s for recording %s", enabled, recording_id)
        return True

    def get_session(self, recording_id: str) -> Optional[RecordingSession]:
        return self._sessions.get(recording_id)

    def list_room_recordings(self, room_code: str) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._sessions.values() if s.room_code == room_code]
