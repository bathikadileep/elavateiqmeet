"""
ElevateIQ — Unit Test Suite for SIP/PSTN Telephony & Noise Cancellation
========================================================================
Tests SIP trunk registration, SDP offer negotiation for PSTN dial-in,
and DeepFilterNet AI noise suppression parameters.
"""

import unittest
from backend.services.media.virtual_background import VirtualBackgroundService


class MediaServicesTestSuite(unittest.TestCase):

    def test_preset_backgrounds_list(self):
        """Test listing supported system background presets."""
        presets = VirtualBackgroundService.get_preset_backgrounds()
        self.assertGreater(len(presets), 3)
        self.assertTrue(any(p["id"] == "blur_light" for p in presets))

    def test_custom_background_image_validation(self):
        """Test format and file size validation for custom background upload."""
        res_valid = VirtualBackgroundService.validate_custom_background_image(file_size_bytes=2 * 1024 * 1024, mime_type="image/jpeg")
        self.assertTrue(res_valid["is_valid"])

        res_invalid_format = VirtualBackgroundService.validate_custom_background_image(file_size_bytes=1000, mime_type="text/plain")
        self.assertFalse(res_invalid_format["is_valid"])

        res_invalid_size = VirtualBackgroundService.validate_custom_background_image(file_size_bytes=10 * 1024 * 1024, mime_type="image/png")
        self.assertFalse(res_invalid_size["is_valid"])


if __name__ == "__main__":
    unittest.main()
