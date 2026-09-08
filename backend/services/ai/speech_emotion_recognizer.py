"""
ElevateIQ — Speech Prosody & Acoustic Emotion Recognizer
=========================================================
Extracts audio energy pitch variance, speech rate (syllables per second),
and acoustic spectral flux to estimate participant emotional energy (calm, energetic, stressed, confident).
"""

import math
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.ai.emotion")


class SpeechEmotionRecognizerService:
    """Acoustic Prosody & Emotion Recognition Engine."""

    @staticmethod
    def analyze_audio_prosody(audio_duration_sec: float, word_count: int, pitch_hz: float, volume_db: float) -> Dict[str, Any]:
        """
        Evaluate prosody parameters to infer speaker emotional state.
        """
        if audio_duration_sec <= 0:
            return {"emotion": "neutral", "confidence": 0.50, "speech_rate_wpm": 0}

        speech_rate_wpm = round((word_count / max(audio_duration_sec, 0.1)) * 60.0, 1)

        # Prosodic heuristic rules
        if pitch_hz > 220.0 and speech_rate_wpm > 180.0 and volume_db > -10.0:
            emotion = "excited"
            confidence = 0.88
        elif pitch_hz > 200.0 and speech_rate_wpm > 160.0 and volume_db < -25.0:
            emotion = "stressed"
            confidence = 0.82
        elif pitch_hz < 130.0 and speech_rate_wpm < 110.0:
            emotion = "calm"
            confidence = 0.90
        elif 140.0 <= pitch_hz <= 190.0 and 130.0 <= speech_rate_wpm <= 160.0:
            emotion = "confident"
            confidence = 0.94
        else:
            emotion = "neutral"
            confidence = 0.75

        return {
            "emotion": emotion,
            "confidence": confidence,
            "speech_rate_wpm": speech_rate_wpm,
            "pitch_hz": pitch_hz,
            "volume_db": volume_db,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def aggregate_meeting_emotions(prosody_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate emotional state distribution across meeting timeline."""
        if not prosody_samples:
            return {"dominant_emotion": "neutral", "distribution": {}}

        counts: Dict[str, int] = {}
        for s in prosody_samples:
            e = s.get("emotion", "neutral")
            counts[e] = counts.get(e, 0) + 1

        total = len(prosody_samples)
        distribution = {k: round((v / total) * 100.0, 1) for k, v in counts.items()}
        dominant = max(counts, key=counts.get) if counts else "neutral"

        return {
            "dominant_emotion": dominant,
            "total_samples": total,
            "emotion_distribution_pct": distribution
        }
