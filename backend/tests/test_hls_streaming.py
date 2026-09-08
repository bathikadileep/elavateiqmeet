import unittest
import os
import tempfile
from backend.services.hls_transcoder import HLSTranscoderService


class HLSStreamingTestSuite(unittest.TestCase):

    def setUp(self):
        self.service = HLSTranscoderService()
        self.temp_dir = tempfile.mkdtemp()
        self.fake_mp4 = os.path.join(self.temp_dir, "test.mp4")
        with open(self.fake_mp4, "wb") as f:
            f.write(b"fake mp4 video content header")

    def test_hls_playlist_generation(self):
        """Test generating HLS master and media playlists."""
        res = self.service.generate_hls_playlist(
            source_mp4_path=self.fake_mp4,
            output_dir=os.path.join(self.temp_dir, "hls")
        )

        self.assertEqual(res["status"], "ready")
        self.assertTrue(os.path.exists(res["master_playlist"]))
        self.assertIn("720p", res["variants"])


if __name__ == "__main__":
    unittest.main()
