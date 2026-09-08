"""
ElevateIQ — Unit Tests for Multi-Track Audio Mixer Service
============================================================
Tests channel addition/removal, decibel/linear conversion, RMS & peak measurement,
EBU R128 LUFS loudness calculation, priority ducking, solo/mute matrix, and peak limiting.
"""

import math
import unittest
from backend.services.media.audio_mixer_service import AudioMixerService, AudioChannel


class TestAudioMixerService(unittest.TestCase):

    def setUp(self):
        self.mixer = AudioMixerService(room_code="room-mix-202", target_lufs=-14.0)

    def test_add_and_remove_channel(self):
        ch = self.mixer.add_channel(
            channel_id="ch_1",
            user_id="u1",
            label="Host Mic",
            is_priority=True,
            target_bus="master"
        )
        self.assertEqual(ch.channel_id, "ch_1")
        self.assertTrue(ch.is_priority)
        self.assertIn("ch_1", self.mixer.channels)
        self.assertIn("ch_1", self.mixer.buses["master"].channels)

        # Remove
        removed = self.mixer.remove_channel("ch_1")
        self.assertTrue(removed)
        self.assertNotIn("ch_1", self.mixer.channels)
        self.assertNotIn("ch_1", self.mixer.buses["master"].channels)

    def test_db_linear_conversions(self):
        # 0 dB = 1.0 linear
        self.assertAlmostEqual(self.mixer.db_to_linear(0.0), 1.0, places=4)
        self.assertAlmostEqual(self.mixer.linear_to_db(1.0), 0.0, places=4)

        # -6 dB ~ 0.5 linear
        self.assertAlmostEqual(self.mixer.db_to_linear(-6.0), 0.501, places=2)
        # +6 dB ~ 2.0 linear
        self.assertAlmostEqual(self.mixer.db_to_linear(6.0), 1.995, places=2)

    def test_calculate_rms_and_peak(self):
        # Sine wave mock
        samples = [0.5, -0.5, 0.5, -0.5]
        rms, peak = self.mixer.calculate_rms_and_peak(samples)
        self.assertAlmostEqual(rms, 0.5, places=4)
        self.assertEqual(peak, 0.5)

        # Empty
        empty_rms, empty_peak = self.mixer.calculate_rms_and_peak([])
        self.assertEqual(empty_rms, 0.0)
        self.assertEqual(empty_peak, 0.0)

    def test_compute_integrated_lufs(self):
        # Silence
        silence = [0.0] * 960
        self.assertEqual(self.mixer.compute_integrated_lufs(silence), -70.0)

        # Normalized full-scale tone (RMS ~ 0.707) -> LUFS ~ -3.7
        full_tone = [0.707] * 960
        lufs = self.mixer.compute_integrated_lufs(full_tone)
        self.assertAlmostEqual(lufs, -3.7, delta=0.5)

    def test_loudness_normalization_delta(self):
        # Audio at -24 LUFS, target is -14 LUFS -> needs +10 dB boost
        # An RMS of ~0.07 corresponds to approx -24 LUFS
        pcm = [0.07] * 960
        delta_db = self.mixer.normalize_loudness_gain(pcm, target_lufs=-14.0)
        self.assertGreater(delta_db, 0.0)
        self.assertLessEqual(delta_db, 18.0)

    def test_priority_ducking_mechanism(self):
        # Channel 1: Priority presenter
        # Channel 2: Background music
        self.mixer.add_channel("ch_pres", "host", "Presenter", is_priority=True)
        self.mixer.add_channel("ch_music", "bg", "Music", is_priority=False)

        # Frame 1: Presenter active (> threshold 0.02)
        frame_active_presenter = {
            "ch_pres": [0.3] * 960,
            "ch_music": [0.4] * 960
        }
        mixed = self.mixer.mix_frame(frame_active_presenter)
        self.assertTrue(self.mixer.is_ducking_active)
        # Music should be ducked by -12dB (~0.25x amplitude).
        # Normal sum without ducking would be 0.3 + 0.4 = 0.7
        # Ducked sum is 0.3 + 0.4 * 0.251 = ~0.40
        self.assertLess(mixed[0], 0.6)

        # Frame 2: Presenter silent
        frame_silent_presenter = {
            "ch_pres": [0.001] * 960,
            "ch_music": [0.4] * 960
        }
        mixed_unducked = self.mixer.mix_frame(frame_silent_presenter)
        self.assertFalse(self.mixer.is_ducking_active)
        self.assertAlmostEqual(mixed_unducked[0], 0.4, places=2)

    def test_mute_and_solo_behavior(self):
        self.mixer.add_channel("ch_1", "u1", "Track 1")
        self.mixer.add_channel("ch_2", "u2", "Track 2")

        # Test Mute
        self.mixer.set_channel_mute("ch_1", True)
        frame = {
            "ch_1": [0.5] * 960,
            "ch_2": [0.2] * 960
        }
        mixed = self.mixer.mix_frame(frame)
        # ch_1 muted, only ch_2 present
        self.assertAlmostEqual(mixed[0], 0.2, places=2)

        # Unmute ch_1 and Solo ch_1
        self.mixer.set_channel_mute("ch_1", False)
        self.mixer.set_channel_solo("ch_1", True)
        mixed_solo = self.mixer.mix_frame(frame)
        # Only ch_1 should be heard
        self.assertAlmostEqual(mixed_solo[0], 0.5, places=2)

    def test_soft_knee_peak_limiter(self):
        # Input sum that would exceed 1.0 (digital clip)
        sample_overdrive = 1.5
        limited = self.mixer.apply_soft_knee_limiter(sample_overdrive, ceiling_db=-1.0)
        # Ceiling of -1dB is ~0.891
        ceiling = self.mixer.db_to_linear(-1.0)
        self.assertLessEqual(limited, ceiling)
        self.assertGreater(limited, 0.0)

    def test_get_mixer_status(self):
        self.mixer.add_channel("ch_diag", "u1", "Diag Track")
        status = self.mixer.get_mixer_status()
        self.assertEqual(status["room_code"], "room-mix-202")
        self.assertEqual(status["channel_count"], 1)
        self.assertIn("ch_diag", status["channels"])
        self.assertIn("master", status["buses"])


if __name__ == "__main__":
    unittest.main()
