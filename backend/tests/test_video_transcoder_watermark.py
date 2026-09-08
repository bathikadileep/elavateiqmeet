"""
ElevateIQ — Unit Test Suite for Video Transcoder Watermarking & Presets
========================================================================
Tests target preset configuration (1080p, 720p, 360p) and watermark text overlays.
"""

import unittest
from backend.services.recording_transcoder import RecordingTranscoderEngine


class VideoTranscoderWatermarkTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = RecordingTranscoderEngine()

    def test_preset_resolution_mapping(self):
        """Test preset resolution and bitrate settings."""
        job = self.engine.submit_transcode_job("rec_wm_101", ["seg1.webm"], target_preset="1080p")
        self.assertEqual(job["resolution"], "1920x1080")

        job_360 = self.engine.submit_transcode_job("rec_wm_102", ["seg1.webm"], target_preset="360p")
        self.assertEqual(job_360["resolution"], "640x360")

    def test_watermark_text_overlay(self):
        """Test embedding watermark text into transcode job payload."""
        job = self.engine.submit_transcode_job(
            recording_id="rec_wm_103",
            input_segments=["seg1.webm"],
            target_preset="720p",
            watermark_text="ElevateIQ Enterprise Confidential"
        )
        self.assertEqual(job["watermark"], "ElevateIQ Enterprise Confidential")


if __name__ == "__main__":
    unittest.main()
