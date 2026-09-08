"""
ElevateIQ — Unit Test Suite for AI Noise Cancellation & AEC Engine
====================================================================
Tests PCM audio frame processing, SNR boost estimation, VAD speech detection, and AEC configuration.
"""

import unittest
from backend.services.noise_cancellation_engine import NoiseCancellationEngine


class NoiseCancellationTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = NoiseCancellationEngine(suppression_level_db=-25.0)

    def test_audio_frame_dsp_processing(self):
        """Test processing 10ms PCM audio frame with speech enhancement."""
        sample_pcm = b"\x00\x10\x00\x20\x00\x15" * 160  # 960 bytes
        res = self.engine.process_pcm_audio_frame(sample_pcm, enable_speech_enhancement=True)

        self.assertEqual(res["sample_rate_hz"], 48000)
        self.assertGreater(res["snr_improvement_db"], 15.0)
        self.assertEqual(res["suppression_mode"], "DEEP_FILTER_NET_3")

    def test_aec_configuration(self):
        """Test configuring Acoustic Echo Cancellation parameters."""
        config = self.engine.configure_aec_settings(filter_length_ms=160, enable_double_talk_detection=True)
        self.assertEqual(config["filter_length_ms"], 160)
        self.assertTrue(config["enable_double_talk_detection"])
        self.assertEqual(config["non_linear_processing_level"], "AGGRESSIVE")


if __name__ == "__main__":
    unittest.main()
