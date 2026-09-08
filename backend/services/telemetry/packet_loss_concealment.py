"""
ElevateIQ — Packet Loss Concealment (PLC) Audio Engine
======================================================
Implements G.711 Appendix I and pitch-synchronous waveform extrapolation
for WebRTC audio packet loss concealment. Synthesizes missing audio frames
during bursts of packet loss to prevent audible robotic clicks and dropout gaps.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class ConcealmentState(str, Enum):
    NORMAL = "normal"              # Regular packet received
    CONCEALING = "concealing"      # Synthesizing lost frame
    RECOVERY = "recovery"          # Smoothing transition back to real packet


@dataclass
class AudioFrame:
    """PCM audio frame."""
    sequence_number: int
    timestamp_ms: int
    samples: List[float]          # Normalized float [-1.0, 1.0]
    sample_rate_hz: int = 16000
    is_concealed: bool = False

    @property
    def num_samples(self) -> int:
        return len(self.samples)

    @property
    def duration_ms(self) -> float:
        return (len(self.samples) / self.sample_rate_hz) * 1000.0

    @property
    def rms_energy(self) -> float:
        if not self.samples:
            return 0.0
        sum_sq = sum(s * s for s in self.samples)
        return math.sqrt(sum_sq / len(self.samples))


@dataclass
class PLCStats:
    total_frames_received: int = 0
    total_frames_lost: int = 0
    total_frames_concealed: int = 0
    max_consecutive_lost: int = 0
    current_consecutive_lost: int = 0
    attenuation_factor: float = 1.0

    @property
    def loss_rate(self) -> float:
        total = self.total_frames_received + self.total_frames_lost
        return (self.total_frames_lost / total) if total > 0 else 0.0


class PacketLossConcealmentEngine:
    """
    Pitch-synchronous waveform extrapolation for WebRTC audio streams.
    When a packet is lost, extrapolates the pitch period from previous frames
    with exponential decay attenuation to prevent persistent buzz artifacts.
    """

    # Maximum consecutive frames to synthesize before muting (60 ms typical)
    MAX_CONCEAL_FRAMES = 6
    DECAY_PER_FRAME = 0.82       # ~20% volume drop per synthesized frame
    MIN_PITCH_HZ = 60.0
    MAX_PITCH_HZ = 400.0

    def __init__(self, sample_rate_hz: int = 16000, frame_size_ms: int = 10) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.frame_size_ms = frame_size_ms
        self.samples_per_frame = int((sample_rate_hz * frame_size_ms) / 1000)

        self._history_buffer: List[float] = []
        self._max_history = self.samples_per_frame * 10   # 100 ms history
        self._state = ConcealmentState.NORMAL
        self._stats = PLCStats()
        self._last_pitch_period_samples: int = self.samples_per_frame
        self._consecutive_lost: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_frame(self, frame: AudioFrame) -> AudioFrame:
        """
        Process a normal (received) audio frame.
        Smooths transition if coming out of concealment state.
        """
        self._stats.total_frames_received += 1
        self._consecutive_lost = 0

        # If recovering from concealment, apply overlap-add smoothing
        if self._state == ConcealmentState.CONCEALING:
            self._state = ConcealmentState.RECOVERY
            frame = self._smooth_recovery(frame)
        else:
            self._state = ConcealmentState.NORMAL

        self._append_to_history(frame.samples)
        self._estimate_pitch_period()
        return frame

    def conceal_lost_frame(self, expected_seq: int, expected_timestamp_ms: int) -> AudioFrame:
        """
        Generate a synthesized replacement frame for a lost packet.
        Uses pitch-synchronous waveform repetition with exponential decay.
        """
        self._stats.total_frames_lost += 1
        self._stats.total_frames_concealed += 1
        self._consecutive_lost += 1
        self._stats.current_consecutive_lost = self._consecutive_lost
        if self._consecutive_lost > self._stats.max_consecutive_lost:
            self._stats.max_consecutive_lost = self._consecutive_lost

        self._state = ConcealmentState.CONCEALING

        # If too many consecutive frames are lost, mute to comfort noise
        if self._consecutive_lost > self.MAX_CONCEAL_FRAMES:
            synthesized = [0.0] * self.samples_per_frame
        else:
            attenuation = self.DECAY_PER_FRAME ** self._consecutive_lost
            self._stats.attenuation_factor = attenuation
            synthesized = self._extrapolate_waveform(attenuation)

        self._append_to_history(synthesized)

        return AudioFrame(
            sequence_number=expected_seq,
            timestamp_ms=expected_timestamp_ms,
            samples=synthesized,
            sample_rate_hz=self.sample_rate_hz,
            is_concealed=True,
        )

    # ------------------------------------------------------------------
    # Waveform Extrapolation & Pitch Estimation
    # ------------------------------------------------------------------

    def _estimate_pitch_period(self) -> None:
        """
        Estimate dominant pitch period via autocorrelation on history buffer.
        """
        if len(self._history_buffer) < self.samples_per_frame * 3:
            return

        min_lag = int(self.sample_rate_hz / self.MAX_PITCH_HZ)
        max_lag = int(self.sample_rate_hz / self.MIN_PITCH_HZ)
        max_lag = min(max_lag, len(self._history_buffer) // 2)

        best_lag = self.samples_per_frame
        best_corr = -1.0
        signal = self._history_buffer

        for lag in range(min_lag, max_lag, 2):
            corr = 0.0
            norm_a = 0.0
            norm_b = 0.0
            n = min(len(signal) - lag, self.samples_per_frame * 2)
            for i in range(n):
                s1 = signal[len(signal) - 1 - i]
                s2 = signal[len(signal) - 1 - i - lag]
                corr += s1 * s2
                norm_a += s1 * s1
                norm_b += s2 * s2

            norm = math.sqrt(norm_a * norm_b) if (norm_a > 0 and norm_b > 0) else 1e-9
            normalized_corr = corr / norm
            if normalized_corr > best_corr:
                best_corr = normalized_corr
                best_lag = lag

        self._last_pitch_period_samples = max(best_lag, 1)

    def _extrapolate_waveform(self, attenuation: float) -> List[float]:
        """
        Copy the last pitch cycle repeatedly, scaled by attenuation factor.
        """
        period = self._last_pitch_period_samples
        if not self._history_buffer or period <= 0:
            return [0.0] * self.samples_per_frame

        synthesized = []
        hist_len = len(self._history_buffer)
        for i in range(self.samples_per_frame):
            # Index into history by pitch period cycle
            offset = (i % period) + 1
            src_idx = max(0, hist_len - offset)
            sample = self._history_buffer[src_idx] * attenuation
            # Add a slight high-frequency damping
            if i > 0 and synthesized:
                sample = 0.85 * sample + 0.15 * synthesized[-1]
            synthesized.append(sample)

        return synthesized

    def _smooth_recovery(self, frame: AudioFrame) -> AudioFrame:
        """
        Cross-fade the start of the first good frame with the end of concealment
        to avoid phase jump clicks.
        """
        overlap_samples = min(self.samples_per_frame // 4, len(frame.samples))
        if overlap_samples <= 0 or not self._history_buffer:
            return frame

        smoothed = list(frame.samples)
        hist_end = self._history_buffer[-overlap_samples:]

        for i in range(overlap_samples):
            w_good = i / overlap_samples
            w_hist = 1.0 - w_good
            h_sample = hist_end[i] if i < len(hist_end) else 0.0
            smoothed[i] = w_good * frame.samples[i] + w_hist * h_sample

        return AudioFrame(
            sequence_number=frame.sequence_number,
            timestamp_ms=frame.timestamp_ms,
            samples=smoothed,
            sample_rate_hz=frame.sample_rate_hz,
            is_concealed=False,
        )

    def _append_to_history(self, samples: List[float]) -> None:
        self._history_buffer.extend(samples)
        if len(self._history_buffer) > self._max_history:
            self._history_buffer = self._history_buffer[-self._max_history:]

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    @property
    def stats(self) -> PLCStats:
        return self._stats

    def reset_stats(self) -> None:
        self._stats = PLCStats()
