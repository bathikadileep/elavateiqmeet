"""
ElevateIQ SFU — Voice Activity Detection (VAD) Engine
======================================================
Calculates real-time audio energy (dBFS), identifies active speakers,
and dispatches VAD speaker events across meeting rooms.
"""

import math
import time
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("elevateiq.sfu.vad")


class VADEvent:
    """Represents a Voice Activity Event."""
    def __init__(self, sid: str, user_id: Optional[str], display_name: str, audio_level_dbfs: float, is_speaking: bool):
        self.sid = sid
        self.user_id = user_id
        self.display_name = display_name
        self.audio_level_dbfs = audio_level_dbfs  # -100 to 0 dBFS
        self.audio_level_normalized = self._normalize_dbfs(audio_level_dbfs)  # 0 to 100%
        self.is_speaking = is_speaking
        self.timestamp = time.time()

    @staticmethod
    def _normalize_dbfs(dbfs: float) -> int:
        """Converts -100 dBFS -> 0 dBFS into 0% -> 100% scale."""
        if dbfs <= -90.0:
            return 0
        if dbfs >= 0.0:
            return 100
        return int(((dbfs + 90.0) / 90.0) * 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sid": self.sid,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "audio_level_dbfs": round(self.audio_level_dbfs, 1),
            "audio_level_percent": self.audio_level_normalized,
            "is_speaking": self.is_speaking,
            "timestamp": self.timestamp
        }


class VoiceActivityDetector:
    """
    Manages active speaker election across a room's audio producers.
    """
    def __init__(self, speaking_threshold_dbfs: float = -45.0):
        self.speaking_threshold_dbfs = speaking_threshold_dbfs
        self.active_speaker_sid: Optional[str] = None
        self.active_speaker_name: Optional[str] = None
        self.last_speech_time = 0.0

    def process_audio_energy(
        self, sid: str, display_name: str, user_id: Optional[str], dbfs: float
    ) -> Optional[VADEvent]:
        """
        Process audio energy level and return VADEvent if speaker state changes.
        """
        is_speaking = dbfs > self.speaking_threshold_dbfs

        if is_speaking:
            if self.active_speaker_sid != sid:
                self.active_speaker_sid = sid
                self.active_speaker_name = display_name
                self.last_speech_time = time.time()
                log.debug("Active speaker elected: %s (%s)", display_name, sid)
                return VADEvent(sid, user_id, display_name, dbfs, is_speaking=True)

        return VADEvent(sid, user_id, display_name, dbfs, is_speaking=is_speaking)
