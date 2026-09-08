"""
ElevateIQ — Unit Test Suite for Screen Share Video Grid Compositor
==================================================================
Tests computing canvas layout coordinates for picture-in-picture video streams.
"""

import unittest
from backend.services.media.screen_share_compositor import ScreenShareCompositor


class ScreenShareCompositorTestSuite(unittest.TestCase):

    def setUp(self):
        self.compositor = ScreenShareCompositor()

    def test_screen_share_layout(self):
        """Test computing layout when screen share is active."""
        res = self.compositor.compute_canvas_layout(screen_share_active=True, speaker_count=3)
        self.assertEqual(res["canvas"]["width"], 1920)
        self.assertEqual(res["tiles"][0]["type"], "SCREEN_SHARE")


if __name__ == "__main__":
    unittest.main()
