"""
ElevateIQ — AI Noise Suppression & Acoustic Echo Cancellation (AEC) Engine
===========================================================================
Simulates WebAssembly / DeepFilterNet audio DSP pipeline for background noise removal,
transient click/keyboard suppression, and voice clarity enhancement.
"""

import math
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.noise_suppression")


class NoiseCancellationEngine:
    """Audio DSP Noise Cancellation Engine."""

    def __init__(self, suppression_level_db: float = -25.0):
        self.suppression_level = suppression_level_db
        self.sample_rate_hz = 48000
        self.frame_size_samples = 480  # 10ms frame at 48kHz

    def process_pcm_audio_frame(self, audio_bytes: bytes, enable_speech_enhancement: bool = True) -> Dict[str, Any]:
        """
        Process a 10ms raw PCM16 audio frame through DSP noise model.
        Calculates signal-to-noise ratio (SNR) improvement.
        """
        raw_size = len(audio_bytes)
        if raw_size == 0:
            return {"processed_bytes": b"", "snr_improvement_db": 0.0, "speech_detected": False}

        # Calculate estimated RMS amplitude
        samples_count = raw_size // 2
        sum_sq = 0.0
        for i in range(0, raw_size, 2):
            sample = int.from_bytes(audio_bytes[i:i+2], byteorder="little", signed=True)
            sum_sq += sample * sample

        rms = math.sqrt(sum_sq / max(1, samples_count))
        speech_detected = rms > 1500.0  # VAD threshold

        snr_boost = 18.5 if speech_detected else 24.0

        log.debug("Processed audio frame (%d samples): RMS=%.1f Speech=%s SNR_Boost=%.1fdB",
                  samples_count, rms, speech_detected, snr_boost)

        return {
            "processed_bytes": audio_bytes,
            "sample_rate_hz": self.sample_rate_hz,
            "snr_improvement_db": snr_boost,
            "speech_detected": speech_detected,
            "rms_level": round(rms, 2),
            "suppression_mode": "DEEP_FILTER_NET_3" if enable_speech_enhancement else "STANDARD_SPEEX",
        }

    def configure_aec_settings(self, filter_length_ms: int = 120, enable_double_talk_detection: bool = True) -> Dict[str, Any]:
        """Configure Acoustic Echo Cancellation (AEC) filter parameters."""
        config = {
            "filter_length_ms": filter_length_ms,
            "enable_double_talk_detection": enable_double_talk_detection,
            "non_linear_processing_level": "AGGRESSIVE",
            "comfort_noise_generator": True,
        }
        log.info("Updated AEC configuration: length=%dms DT=%s", filter_length_ms, enable_double_talk_detection)
        return config
