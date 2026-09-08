"""
ElevateIQ — Unit Test Suite for WebGL Filter Processor
======================================================
Tests WebGL video filter preset uniforms configuration.
"""

import unittest
from backend.services.media.webgl_filter_processor import WebGLFilterProcessor


class WebGLFilterProcessorTestSuite(unittest.TestCase):

    def setUp(self):
        self.processor = WebGLFilterProcessor()

    def test_low_light_filter_uniforms(self):
        """Test applying low light video filter preset."""
        res = self.processor.apply_filter_preset("low_light", intensity=0.8)
        self.assertEqual(res["filter"], "low_light")
        self.assertIn("brightness", res["uniforms"])


if __name__ == "__main__":
    unittest.main()
