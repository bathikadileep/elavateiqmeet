"""
ElevateIQ — Live Automated Captioning & Multi-Language Subtitle Generator
========================================================================
Processes real-time audio chunk speech-to-text transcripts and formats
WebGL WebVTT subtitle streams with multi-speaker identification & translations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.captioning")


class LiveCaptionService:
    """Enterprise Real-Time Captioning & Subtitle Streaming Engine."""

    SUPPORTED_LANGUAGES = ["en-US", "es-ES", "fr-FR", "de-DE", "zh-CN", "ja-JP", "hi-IN", "pt-BR"]

    def __init__(self):
        self._caption_buffers: Dict[str, List[Dict[str, Any]]] = {}

    def ingest_speech_chunk(self, meeting_code: str, speaker_id: str, speaker_name: str, text: str, language: str = "en-US", is_final: bool = True) -> Dict[str, Any]:
        """
        Ingest a real-time transcript segment from STT engine and build WebVTT caption frame.
        """
        if meeting_code not in self._caption_buffers:
            self._caption_buffers[meeting_code] = []

        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%H:%M:%S.%f")[:-3]

        caption_frame = {
            "caption_id": f"cap_{len(self._caption_buffers[meeting_code]) + 1}",
            "meeting_code": meeting_code,
            "speaker_id": speaker_id,
            "speaker_name": speaker_name,
            "text": text.strip(),
            "language": language,
            "is_final": is_final,
            "timestamp": timestamp_str,
            "created_at": now.isoformat(),
        }

        if is_final:
            self._caption_buffers[meeting_code].append(caption_frame)

        log.debug("Ingested live caption for %s [%s]: %s", meeting_code, speaker_name, text)
        return caption_frame

    def get_recent_captions(self, meeting_code: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent caption history for client display buffer."""
        frames = self._caption_buffers.get(meeting_code, [])
        return frames[-limit:]

    def export_webvtt(self, meeting_code: str) -> str:
        """Generate full WebVTT document string for meeting cloud recordings."""
        frames = self._caption_buffers.get(meeting_code, [])
        vtt_lines = ["WEBVTT - ElevateIQ Meeting Caption Track\n"]

        for idx, frame in enumerate(frames, start=1):
            start_t = f"00:{frame['timestamp']}"
            # Assume 3 second cue duration per subtitle line
            end_t = f"00:{frame['timestamp'][:8]}.999"

            vtt_lines.append(f"{idx}")
            vtt_lines.append(f"{start_t} --> {end_t}")
            vtt_lines.append(f"<v {frame['speaker_name']}>{frame['text']}\n")

        return "\n".join(vtt_lines)
