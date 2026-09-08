"""
Recording Thumbnail Extractor
==============================
Extracts preview thumbnails from meeting recordings at fixed intervals.
Simulates ffmpeg subprocess for frame extraction and generates metadata.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ThumbnailFormat(str, Enum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"


class ThumbnailQuality(str, Enum):
    LOW = "low"        # 160x90
    MEDIUM = "medium"  # 320x180
    HIGH = "high"      # 640x360
    FULL = "full"      # 1280x720


_QUALITY_DIMS: Dict[ThumbnailQuality, Tuple[int, int]] = {
    ThumbnailQuality.LOW: (160, 90),
    ThumbnailQuality.MEDIUM: (320, 180),
    ThumbnailQuality.HIGH: (640, 360),
    ThumbnailQuality.FULL: (1280, 720),
}


@dataclass
class Thumbnail:
    thumbnail_id: str
    recording_id: str
    timestamp_ms: int
    frame_number: int
    file_path: str
    format: ThumbnailFormat
    width: int
    height: int
    file_size_bytes: int
    is_cover: bool = False
    generated_at: float = field(default_factory=time.time)
    checksum_md5: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thumbnail_id": self.thumbnail_id,
            "recording_id": self.recording_id,
            "timestamp_ms": self.timestamp_ms,
            "frame_number": self.frame_number,
            "file_path": self.file_path,
            "format": self.format.value,
            "width": self.width,
            "height": self.height,
            "file_size_bytes": self.file_size_bytes,
            "is_cover": self.is_cover,
            "generated_at": self.generated_at,
            "checksum_md5": self.checksum_md5,
        }


@dataclass
class ThumbnailStrip:
    """WebVTT-compatible thumbnail sprite strip."""
    recording_id: str
    strip_path: str
    vtt_path: str
    total_thumbnails: int
    interval_ms: int
    duration_ms: int
    strip_width: int
    strip_height: int
    cols: int
    rows: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recording_id": self.recording_id,
            "strip_path": self.strip_path,
            "vtt_path": self.vtt_path,
            "total_thumbnails": self.total_thumbnails,
            "interval_ms": self.interval_ms,
            "duration_ms": self.duration_ms,
            "strip_width": self.strip_width,
            "strip_height": self.strip_height,
            "cols": self.cols,
            "rows": self.rows,
        }


@dataclass
class ExtractionJob:
    job_id: str
    recording_id: str
    source_path: str
    output_dir: str
    interval_seconds: float
    quality: ThumbnailQuality
    fmt: ThumbnailFormat
    status: str = "pending"
    thumbnails: List[Thumbnail] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def duration_ms(self) -> int:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at) * 1000)
        return 0


class RecordingThumbnailExtractor:
    """
    Extracts preview thumbnails from recording files.
    In production: wraps ffmpeg subprocess.
    In simulation: produces metadata-complete thumbnail descriptors.
    """

    def __init__(
        self,
        output_base_dir: str = "/var/elviq/thumbnails",
        default_interval: float = 10.0,   # seconds
        default_quality: ThumbnailQuality = ThumbnailQuality.MEDIUM,
        default_format: ThumbnailFormat = ThumbnailFormat.JPEG,
        ffmpeg_path: str = "ffmpeg",
    ) -> None:
        self.output_base_dir = output_base_dir
        self.default_interval = default_interval
        self.default_quality = default_quality
        self.default_format = default_format
        self.ffmpeg_path = ffmpeg_path
        self._jobs: Dict[str, ExtractionJob] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_extraction(
        self,
        recording_id: str,
        source_path: str,
        duration_seconds: float,
        interval_seconds: Optional[float] = None,
        quality: Optional[ThumbnailQuality] = None,
        fmt: Optional[ThumbnailFormat] = None,
        output_dir: Optional[str] = None,
    ) -> ExtractionJob:
        interval = interval_seconds or self.default_interval
        q = quality or self.default_quality
        f = fmt or self.default_format
        out_dir = output_dir or os.path.join(self.output_base_dir, recording_id)

        job_id = f"thumb_{recording_id}_{uuid.uuid4().hex[:8]}"
        job = ExtractionJob(
            job_id=job_id,
            recording_id=recording_id,
            source_path=source_path,
            output_dir=out_dir,
            interval_seconds=interval,
            quality=q,
            fmt=f,
        )
        self._jobs[job_id] = job
        self._execute_job(job, duration_seconds)
        return job

    def get_job(self, job_id: str) -> Optional[ExtractionJob]:
        return self._jobs.get(job_id)

    def get_thumbnails(self, recording_id: str) -> List[Thumbnail]:
        thumbnails = []
        for job in self._jobs.values():
            if job.recording_id == recording_id:
                thumbnails.extend(job.thumbnails)
        return sorted(thumbnails, key=lambda t: t.timestamp_ms)

    def get_cover_thumbnail(self, recording_id: str) -> Optional[Thumbnail]:
        thumbnails = self.get_thumbnails(recording_id)
        for t in thumbnails:
            if t.is_cover:
                return t
        return thumbnails[0] if thumbnails else None

    # ------------------------------------------------------------------
    # Thumbnail strip (sprite) generation
    # ------------------------------------------------------------------

    def generate_thumbnail_strip(
        self,
        recording_id: str,
        thumbnails: Optional[List[Thumbnail]] = None,
        cols: int = 10,
    ) -> ThumbnailStrip:
        thumbs = thumbnails or self.get_thumbnails(recording_id)
        n = len(thumbs)
        rows = math.ceil(n / cols) if n > 0 else 1
        q = self.default_quality
        w, h = _QUALITY_DIMS[q]
        strip_path = os.path.join(self.output_base_dir, recording_id, "strip.jpg")
        vtt_path = os.path.join(self.output_base_dir, recording_id, "thumbnails.vtt")
        duration = thumbs[-1].timestamp_ms if thumbs else 0
        interval = int(self.default_interval * 1000)

        return ThumbnailStrip(
            recording_id=recording_id,
            strip_path=strip_path,
            vtt_path=vtt_path,
            total_thumbnails=n,
            interval_ms=interval,
            duration_ms=duration,
            strip_width=w * min(cols, n),
            strip_height=h * rows,
            cols=cols,
            rows=rows,
        )

    def generate_vtt_content(self, strip: ThumbnailStrip) -> str:
        """Generate WebVTT thumbnail track content."""
        lines = ["WEBVTT", ""]
        w, h = _QUALITY_DIMS[self.default_quality]
        for i in range(strip.total_thumbnails):
            start_ms = i * strip.interval_ms
            end_ms = (i + 1) * strip.interval_ms
            col = i % strip.cols
            row = i // strip.cols
            x_offset = col * w
            y_offset = row * h
            lines.append(f"{self._ms_to_vtt(start_ms)} --> {self._ms_to_vtt(end_ms)}")
            lines.append(f"{strip.strip_path}#xywh={x_offset},{y_offset},{w},{h}")
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal execution (simulation)
    # ------------------------------------------------------------------

    def _execute_job(self, job: ExtractionJob, duration_seconds: float) -> None:
        job.status = "running"
        job.started_at = time.time()
        try:
            thumbnails = self._simulate_extraction(job, duration_seconds)
            job.thumbnails = thumbnails
            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
        finally:
            job.completed_at = time.time()

    def _simulate_extraction(
        self, job: ExtractionJob, duration_seconds: float
    ) -> List[Thumbnail]:
        thumbnails = []
        w, h = _QUALITY_DIMS[job.quality]
        num_frames = max(1, int(duration_seconds / job.interval_seconds))

        for i in range(num_frames):
            ts_ms = int(i * job.interval_seconds * 1000)
            frame_num = int(i * job.interval_seconds * 30)  # 30 fps
            file_name = f"thumb_{i:04d}.{job.fmt.value}"
            file_path = os.path.join(job.output_dir, file_name)
            payload = f"{job.recording_id}:{ts_ms}:{frame_num}"
            checksum = hashlib.md5(payload.encode()).hexdigest()
            est_size = (w * h * 3) // 8  # rough JPEG estimate

            thumb = Thumbnail(
                thumbnail_id=f"th_{uuid.uuid4().hex[:8]}",
                recording_id=job.recording_id,
                timestamp_ms=ts_ms,
                frame_number=frame_num,
                file_path=file_path,
                format=job.fmt,
                width=w,
                height=h,
                file_size_bytes=est_size,
                is_cover=(i == num_frames // 4),  # ~25% mark as cover
                checksum_md5=checksum,
            )
            thumbnails.append(thumb)
        return thumbnails

    @staticmethod
    def _ms_to_vtt(ms: int) -> str:
        s = ms // 1000
        m, sec = divmod(s, 60)
        hh, mm = divmod(m, 60)
        return f"{hh:02d}:{mm:02d}:{sec:02d}.{ms % 1000:03d}"

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        jobs = list(self._jobs.values())
        total_thumbs = sum(len(j.thumbnails) for j in jobs)
        return {
            "total_jobs": len(jobs),
            "completed": sum(1 for j in jobs if j.status == "completed"),
            "failed": sum(1 for j in jobs if j.status == "failed"),
            "total_thumbnails": total_thumbs,
        }
