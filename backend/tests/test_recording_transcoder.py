"""
ElevateIQ — Unit Test Suite for Recording Transcoder Engine
============================================================
Tests submitting transcoding jobs, simulated progress pipelines, and output URLs generation.
"""

import unittest
from backend.services.recording_transcoder import RecordingTranscoderEngine


class RecordingTranscoderTestSuite(unittest.TestCase):

    def setUp(self):
        self.engine = RecordingTranscoderEngine()

    def test_transcode_job_submission(self):
        """Test submitting video transcoding job."""
        job = self.engine.submit_transcode_job(
            recording_id="rec_full_hd_123",
            input_segments=["chunk1.webm", "chunk2.webm"],
            target_preset="1080p",
            watermark_text="Confidential - ElevateIQ"
        )

        self.assertTrue(job["job_id"].startswith("job_tx_"))
        self.assertEqual(job["status"], "QUEUED")
        self.assertEqual(job["resolution"], "1920x1080")

    def test_transcode_simulation_completion(self):
        """Test executing transcode processing pipeline."""
        job = self.engine.submit_transcode_job("rec_720p_456", ["seg1.webm"], "720p")
        job_id = job["job_id"]

        completed = self.engine.simulate_transcode_progress(job_id)
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertEqual(completed["progress_pct"], 100)
        self.assertIn("mp4_url", completed["output_files"])
        self.assertIn("hls_playlist_url", completed["output_files"])


if __name__ == "__main__":
    unittest.main()
