"""
ElevateIQ — Unit Test Suite for Packet Loss Concealment (PLC) Engine
=====================================================================
Tests normal frame processing, pitch estimation, waveform extrapolation,
exponential decay attenuation, and smooth recovery cross-fading.
"""

import math
import unittest
from backend.services.telemetry.packet_loss_concealment import (
    PacketLossConcealmentEngine,
    AudioFrame,
    ConcealmentState,
)


class PacketLossConcealmentTestSuite(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 16000
        self.frame_ms = 10
        self.plc = PacketLossConcealmentEngine(sample_rate_hz=self.sample_rate, frame_size_ms=self.frame_ms)

    def _generate_sine_wave_frame(self, seq: int, ts: int, freq_hz: float = 440.0) -> AudioFrame:
        num_samples = int((self.sample_rate * self.frame_ms) / 1000)
        samples = [
            math.sin(2.0 * math.pi * freq_hz * (i / self.sample_rate))
            for i in range(num_samples)
        ]
        return AudioFrame(
            sequence_number=seq,
            timestamp_ms=ts,
            samples=samples,
            sample_rate_hz=self.sample_rate,
        )

    def test_normal_frame_processing(self):
        """Verify normal audio passes through and history buffer fills."""
        frame = self._generate_sine_wave_frame(1, 1000)
        processed = self.plc.process_frame(frame)

        self.assertFalse(processed.is_concealed)
        self.assertEqual(len(processed.samples), len(frame.samples))
        self.assertEqual(self.plc.stats.total_frames_received, 1)
        self.assertEqual(self.plc.stats.total_frames_lost, 0)

    def test_single_frame_loss_concealment(self):
        """Test synthesizing a single missing audio packet."""
        # Prime the history with 5 clean frames
        for i in range(5):
            self.plc.process_frame(self._generate_sine_wave_frame(i, i * 10))

        # Frame 5 is lost! Conceal it
        lost_frame = self.plc.conceal_lost_frame(expected_seq=5, expected_timestamp_ms=50)

        self.assertTrue(lost_frame.is_concealed)
        self.assertEqual(len(lost_frame.samples), self.plc.samples_per_frame)
        self.assertGreater(lost_frame.rms_energy, 0.0)
        self.assertEqual(self.plc.stats.total_frames_lost, 1)
        self.assertEqual(self.plc.stats.total_frames_concealed, 1)

    def test_burst_loss_attenuation(self):
        """Verify synthesized energy drops exponentially during multi-frame loss."""
        # Prime history
        for i in range(5):
            self.plc.process_frame(self._generate_sine_wave_frame(i, i * 10))

        energies = []
        for i in range(4):
            c_frame = self.plc.conceal_lost_frame(expected_seq=10 + i, expected_timestamp_ms=100 + i * 10)
            energies.append(c_frame.rms_energy)

        # Each consecutive synthesized frame must have lower energy
        for idx in range(len(energies) - 1):
            self.assertGreaterEqual(energies[idx], energies[idx + 1])

    def test_max_consecutive_loss_mutes(self):
        """Verify muting when loss exceeds MAX_CONCEAL_FRAMES (6 frames)."""
        for i in range(5):
            self.plc.process_frame(self._generate_sine_wave_frame(i, i * 10))

        for i in range(self.plc.MAX_CONCEAL_FRAMES + 2):
            c_frame = self.plc.conceal_lost_frame(expected_seq=20 + i, expected_timestamp_ms=200 + i * 10)

        # After MAX_CONCEAL_FRAMES, samples must be zeroed out
        self.assertEqual(c_frame.rms_energy, 0.0)
        self.assertTrue(all(s == 0.0 for s in c_frame.samples))

    def test_recovery_smooth_transition(self):
        """Test cross-fade recovery when good packet arrives after loss."""
        # Prime history
        for i in range(5):
            self.plc.process_frame(self._generate_sine_wave_frame(i, i * 10))

        # Conceal lost frame
        self.plc.conceal_lost_frame(expected_seq=5, expected_timestamp_ms=50)
        self.assertEqual(self.plc._state, ConcealmentState.CONCEALING)

        # Next frame arrives
        next_good = self._generate_sine_wave_frame(6, 60)
        recovered = self.plc.process_frame(next_good)

        self.assertEqual(self.plc._state, ConcealmentState.RECOVERY)
        self.assertFalse(recovered.is_concealed)
        self.assertEqual(len(recovered.samples), self.plc.samples_per_frame)

    def test_loss_rate_calculation(self):
        """Verify loss rate statistic percentage."""
        for i in range(8):
            self.plc.process_frame(self._generate_sine_wave_frame(i, i * 10))

        for i in range(2):
            self.plc.conceal_lost_frame(8 + i, (8 + i) * 10)

        # 2 lost out of 10 total = 20% loss rate
        self.assertAlmostEqual(self.plc.stats.loss_rate, 0.20, places=2)


if __name__ == "__main__":
    unittest.main()
