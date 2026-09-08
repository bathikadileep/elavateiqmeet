"""
ElevateIQ — WebRTC Screen Share Video Grid Compositor
=====================================================
Blends active screen share video track with speaker webcams into 1080p canvas grid layout for cloud recording.
"""

import logging
from typing import Dict, Any, List

log = logging.getLogger("elevateiq.services.media.compositor")


class ScreenShareCompositor:
    """Server-Side Video Canvas Layout Compositor."""

    def compute_canvas_layout(self, screen_share_active: bool, speaker_count: int) -> Dict[str, Any]:
        """Compute pixel coordinates for main screen share window and picture-in-picture speaker tiles."""
        canvas = {"width": 1920, "height": 1080}
        tiles = []

        if screen_share_active:
            # Main screen share takes 80% left canvas
            tiles.append({"type": "SCREEN_SHARE", "x": 0, "y": 0, "width": 1536, "height": 1080})
            # Right sidebar vertical grid for speaker webcams
            tile_h = 1080 // max(speaker_count, 1)
            for i in range(speaker_count):
                tiles.append({"type": "WEBCAM", "x": 1536, "y": i * tile_h, "width": 384, "height": tile_h})
        else:
            # Equal grid layout
            tiles.append({"type": "GRID", "count": speaker_count})

        log.debug("Computed canvas layout for screen_share=%s (Speakers: %d)", screen_share_active, speaker_count)
        return {"canvas": canvas, "tiles": tiles}
