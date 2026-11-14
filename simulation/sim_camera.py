"""
simulation.sim_camera — Simulated Camera
==========================================
Replaces the real Pi camera on Windows for development.
Can use the Windows webcam (via OpenCV) or return a static
test image for automated testing.

Implements hardware.camera.BaseCamera interface.
"""

import logging
import os
from hardware.camera import BaseCamera

logger = logging.getLogger(__name__)


class SimCamera(BaseCamera):
    """
    Simulated camera for Windows development.

    Modes:
      - "webcam"  : Use the system webcam via OpenCV (if available)
      - "static"  : Return a placeholder test image

    TODO: Implement webcam mode with cv2.VideoCapture(0) for
          interactive dev testing.
    """

    def __init__(self, width: int = 640, height: int = 480,
                 mode: str = "static"):
        self.width = width
        self.height = height
        self.mode = mode     # "webcam" or "static"
        self._available = True
        logger.info(f"SimCamera initialised ({width}×{height}, mode={mode}).")

    def init(self) -> None:
        logger.info("SimCamera: camera ready (simulated).")

    def capture_image(self, filepath: str) -> str:
        logger.info(f"📷 SimCamera: captured image → '{filepath}' (simulated).")
        # In static mode, we just log.  In webcam mode, use OpenCV.
        return filepath

    def capture_frame(self) -> bytes:
        logger.debug("SimCamera: returning empty frame (simulated).")
        # Return a minimal valid placeholder (1×1 black pixel JPEG-like)
        return b"\x00" * (self.width * self.height * 3)

    def get_resolution(self) -> tuple:
        return (self.width, self.height)

    def set_resolution(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        logger.info(f"SimCamera: resolution set to {width}×{height}.")

    def is_available(self) -> bool:
        return self._available

    def cleanup(self) -> None:
        logger.info("SimCamera: cleaned up.")
