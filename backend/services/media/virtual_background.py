"""
ElevateIQ — Virtual Background & Video Segmentation Service
============================================================
Handles client and server-side video frame segmentation for background blur (bokeh),
virtual image replacement, and background noise suppression parameters.
"""

import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.media.background")


class VirtualBackgroundService:
    """Virtual Background & Video Masking Processor."""

    @staticmethod
    def get_preset_backgrounds() -> List[Dict[str, str]]:
        """Return list of supported system virtual background templates."""
        return [
            {"id": "blur_light", "name": "Light Blur", "type": "blur", "radius": "5px"},
            {"id": "blur_heavy", "name": "Deep Bokeh", "type": "blur", "radius": "15px"},
            {"id": "office_modern", "name": "Modern Enterprise Office", "type": "image", "url": "/assets/bg/office_modern.jpg"},
            {"id": "studio_minimal", "name": "Minimalist Studio", "type": "image", "url": "/assets/bg/studio_minimal.jpg"},
            {"id": "glassmorphism_blue", "name": "Cyber Cyan Lion Glass", "type": "image", "url": "/assets/bg/glass_lion.jpg"},
        ]

    @staticmethod
    def validate_custom_background_image(file_size_bytes: int, mime_type: str) -> Dict[str, Any]:
        """Validate user uploaded custom background image file."""
        if mime_type not in ["image/jpeg", "image/png", "image/webp"]:
            return {"is_valid": False, "error": "Invalid image format. Must be JPEG, PNG, or WebP."}

        if file_size_bytes > (5 * 1024 * 1024): # 5 MB max
            return {"is_valid": False, "error": "File size exceeds 5 MB limit."}

        return {"is_valid": True, "error": None}
