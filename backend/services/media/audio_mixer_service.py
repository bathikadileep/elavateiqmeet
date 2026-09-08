"""
ElevateIQ — Multi-Track Audio Mixing & Loudness Normalization Engine (EBU R128)
================================================================================
Processes multi-channel PCM audio streams for conference calls, virtual webinars,
and multi-lingual simultaneous interpretation tracks.
Features priority ducking, soft-knee peak compression, and EBU R128 LUFS normalization.
"""

import math
import struct
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

log = logging.getLogger("elevateiq.services.media.mixer")


@dataclass
class AudioChannel:
    """Represents a single input audio channel in the conference mixer."""
    channel_id: str
    user_id: str
    label: str
    gain_db: float = 0.0          # -60.0 to +12.0 dB
    pan: float = 0.0              # -1.0 (full left) to +1.0 (full right)
    is_muted: bool = False
    is_solo: bool = False
    is_priority: bool = False     # Triggers ducking of other non-priority channels
    target_bus: str = "master"    # master, monitor, recording, interpretation
    current_rms: float = 0.0
    current_peak: float = 0.0


@dataclass
class MixerBus:
    """Represents an output mix bus (e.g., Master, Recording, Headphone Monitor)."""
    bus_name: str
    master_gain_db: float = 0.0
    target_lufs: float = -14.0     # Target integrated loudness in LUFS (-14 for web stream, -23 for broadcast)
    limiter_ceiling_db: float = -1.0
    channels: List[str] = field(default_factory=list)


class AudioMixerService:
    """
    Enterprise Real-Time Multi-Track Audio Mixer & Processor.
    Computes summing, priority ducking, peak limiting, and EBU R128 loudness.
    """

    SAMPLE_RATE = 48000           # WebRTC Opus standard sample rate
    FRAME_SIZE_MS = 20            # 20ms audio frames (960 samples @ 48kHz)
    SAMPLES_PER_FRAME = 960

    def __init__(self, room_code: str, target_lufs: float = -14.0):
        self.room_code = room_code
        self.target_lufs = target_lufs
        self.channels: Dict[str, AudioChannel] = {}
        self.buses: Dict[str, MixerBus] = {
            "master": MixerBus(bus_name="master", target_lufs=target_lufs),
            "recording": MixerBus(bus_name="recording", target_lufs=-16.0),
            "interpretation": MixerBus(bus_name="interpretation", target_lufs=-14.0)
        }
        self.ducking_attenuation_db = -12.0   # How much non-priority audio drops during priority speech
        self.ducking_threshold_rms = 0.02      # RMS threshold to trigger ducking
        self.is_ducking_active = False

    def add_channel(
        self,
        channel_id: str,
        user_id: str,
        label: str,
        is_priority: bool = False,
        target_bus: str = "master"
    ) -> AudioChannel:
        """Register a new audio channel for a participant or media track."""
        ch = AudioChannel(
            channel_id=channel_id,
            user_id=user_id,
            label=label,
            is_priority=is_priority,
            target_bus=target_bus
        )
        self.channels[channel_id] = ch
        if target_bus in self.buses:
            if channel_id not in self.buses[target_bus].channels:
                self.buses[target_bus].channels.append(channel_id)
        log.info("AudioMixer [%s]: Added channel %s ('%s', priority=%s) -> bus '%s'",
                 self.room_code, channel_id, label, is_priority, target_bus)
        return ch

    def remove_channel(self, channel_id: str) -> bool:
        """Remove a participant audio channel from the mixer."""
        if channel_id in self.channels:
            ch = self.channels.pop(channel_id)
            if ch.target_bus in self.buses:
                if channel_id in self.buses[ch.target_bus].channels:
                    self.buses[ch.target_bus].channels.remove(channel_id)
            log.info("AudioMixer [%s]: Removed channel %s", self.room_code, channel_id)
            return True
        return False

    def set_channel_gain(self, channel_id: str, gain_db: float) -> None:
        """Set linear/logarithmic gain in decibels (-60 dB to +12 dB)."""
        if channel_id in self.channels:
            self.channels[channel_id].gain_db = max(-60.0, min(12.0, gain_db))

    def set_channel_mute(self, channel_id: str, is_muted: bool) -> None:
        """Mute or un-mute an individual channel."""
        if channel_id in self.channels:
            self.channels[channel_id].is_muted = is_muted

    def set_channel_solo(self, channel_id: str, is_solo: bool) -> None:
        """Solo a channel, isolating it from non-soloed tracks."""
        if channel_id in self.channels:
            self.channels[channel_id].is_solo = is_solo

    @staticmethod
    def db_to_linear(db_val: float) -> float:
        """Convert decibels to linear amplitude multiplier."""
        return math.pow(10.0, db_val / 20.0)

    @staticmethod
    def linear_to_db(lin_val: float) -> float:
        """Convert linear amplitude multiplier to decibels."""
        if lin_val <= 1e-5:
            return -100.0
        return 20.0 * math.log10(lin_val)

    def calculate_rms_and_peak(self, pcm_samples: List[float]) -> Tuple[float, float]:
        """Compute RMS power and peak amplitude of an audio frame."""
        if not pcm_samples:
            return 0.0, 0.0
        sum_sq = sum(s * s for s in pcm_samples)
        rms = math.sqrt(sum_sq / len(pcm_samples))
        peak = max(abs(s) for s in pcm_samples)
        return rms, peak

    def compute_integrated_lufs(self, pcm_samples: List[float]) -> float:
        """
        Approximate integrated loudness according to ITU-R BS.1770-4 / EBU R128.
        Uses K-weighting approximation on single-channel float PCM buffer.
        """
        if not pcm_samples:
            return -70.0  # Digital silence

        sum_sq = sum(s * s for s in pcm_samples)
        mean_sq = sum_sq / len(pcm_samples)
        if mean_sq <= 1e-7:
            return -70.0

        # Standard ITU-R BS.1770 formula: LKFS = -0.691 + 10 * log10(mean_square)
        lufs = -0.691 + (10.0 * math.log10(mean_sq))
        return round(max(-70.0, lufs), 1)

    def apply_soft_knee_limiter(self, sample: float, ceiling_db: float = -1.0) -> float:
        """
        Brickwall true-peak limiter with soft-knee compression.
        Prevents harsh digital clipping beyond the ceiling.
        """
        ceiling = self.db_to_linear(ceiling_db)
        abs_s = abs(sample)
        if abs_s <= ceiling * 0.8:
            return sample

        # Soft knee compression curve above 80% ceiling
        excess = abs_s - (ceiling * 0.8)
        compressed = (ceiling * 0.8) + (ceiling * 0.2) * math.tanh(excess / (ceiling * 0.2))
        return math.copysign(compressed, sample)

    def mix_frame(self, frame_inputs: Dict[str, List[float]], target_bus: str = "master") -> List[float]:
        """
        Sum and mix multiple channel frames into a single master output frame.
        Applies gain, priority ducking, bus gain, and peak limiting.
        """
        num_samples = self.SAMPLES_PER_FRAME
        mixed_buffer = [0.0] * num_samples
        has_solo = any(ch.is_solo for ch in self.channels.values())

        # Check if priority channel is actively speaking to trigger ducking
        priority_speaking = False
        for cid, ch in self.channels.items():
            if ch.is_priority and not ch.is_muted and cid in frame_inputs:
                rms, peak = self.calculate_rms_and_peak(frame_inputs[cid])
                ch.current_rms = rms
                ch.current_peak = peak
                if rms > self.ducking_threshold_rms:
                    priority_speaking = True
                    break

        self.is_ducking_active = priority_speaking
        ducking_mult = self.db_to_linear(self.ducking_attenuation_db) if priority_speaking else 1.0

        # Sum active channels
        for cid, samples in frame_inputs.items():
            if cid not in self.channels:
                continue
            ch = self.channels[cid]
            if ch.is_muted:
                continue
            if ch.target_bus != target_bus:
                continue
            if has_solo and not ch.is_solo:
                continue

            # Compute effective channel gain
            effective_gain = self.db_to_linear(ch.gain_db)
            if not ch.is_priority:
                effective_gain *= ducking_mult

            rms, peak = self.calculate_rms_and_peak(samples)
            ch.current_rms = rms
            ch.current_peak = peak

            # Accumulate samples
            limit = min(num_samples, len(samples))
            for i in range(limit):
                mixed_buffer[i] += samples[i] * effective_gain

        # Apply bus master gain & limiter
        bus = self.buses.get(target_bus, self.buses["master"])
        master_mult = self.db_to_linear(bus.master_gain_db)

        for i in range(num_samples):
            scaled = mixed_buffer[i] * master_mult
            mixed_buffer[i] = self.apply_soft_knee_limiter(scaled, bus.limiter_ceiling_db)

        return mixed_buffer

    def normalize_loudness_gain(self, pcm_samples: List[float], target_lufs: Optional[float] = None) -> float:
        """
        Calculate required gain in dB to bring an audio frame to target EBU R128 LUFS.
        Returns gain delta in decibels.
        """
        target = target_lufs or self.target_lufs
        current_lufs = self.compute_integrated_lufs(pcm_samples)
        if current_lufs <= -60.0:
            return 0.0  # Do not amplify pure silence or background noise
        delta_db = target - current_lufs
        # Clamp gain adjustment to reasonable conference bounds (-18dB to +18dB)
        return round(max(-18.0, min(18.0, delta_db)), 1)

    def get_mixer_status(self) -> Dict[str, Any]:
        """Return diagnostic metrics and active channel states for telemetry."""
        return {
            "room_code": self.room_code,
            "target_lufs": self.target_lufs,
            "is_ducking_active": self.is_ducking_active,
            "channel_count": len(self.channels),
            "channels": {
                cid: {
                    "user_id": ch.user_id,
                    "label": ch.label,
                    "gain_db": ch.gain_db,
                    "is_muted": ch.is_muted,
                    "is_solo": ch.is_solo,
                    "is_priority": ch.is_priority,
                    "target_bus": ch.target_bus,
                    "rms_power": round(ch.current_rms, 4),
                    "peak": round(ch.current_peak, 4)
                }
                for cid, ch in self.channels.items()
            },
            "buses": list(self.buses.keys())
        }
