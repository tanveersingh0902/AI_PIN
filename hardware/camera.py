"""
hardware.camera — Camera Driver
==================================
Controls a camera module attached to the Raspberry Pi for visual
input — image capture, QR/barcode scanning, and (future) basic
vision tasks.

Supports:
  - Raspberry Pi Camera Module v1/v2 (CSI)
  - USB webcams (via V4L2)

On the Pi this uses `picamera2` (the official Pi camera library)
or OpenCV with V4L2 backend.  On Windows the simulation layer
substitutes this module.

NOTE: The Pi Zero W's single-core CPU and 512 MB RAM limit
      real-time video processing.  Use the camera for still
      captures and lightweight frame analysis only.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseCamera(ABC):
    """Interface that both real and simulated cameras implement."""

    @abstractmethod
    def init(self) -> None:
        """Initialise the camera hardware."""
        ...

    @abstractmethod
    def capture_image(self, filepath: str) -> str:
        """
        Capture a still image and save to filepath.

        Returns
        -------
        str
            The path to the saved image file.
        """
        ...

    @abstractmethod
    def capture_frame(self) -> bytes:
        """
        Capture a single frame as raw bytes (JPEG or RGB).

        Returns
        -------
        bytes
            Raw image data.
        """
        ...

    @abstractmethod
    def get_resolution(self) -> tuple:
        """Return the current capture resolution as (width, height)."""
        ...

    @abstractmethod
    def set_resolution(self, width: int, height: int) -> None:
        """Set the capture resolution."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if a camera is detected and usable."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release camera resources."""
        ...


class Camera(BaseCamera):
    """
    Real camera driver for Raspberry Pi.

    Targets:
      - Pi Camera Module v1 (5 MP, CSI)
      - Pi Camera Module v2 (8 MP, CSI)
      - USB webcam (V4L2)

    Dependencies (Pi only):
      - picamera2   (official Pi camera library)
      - opencv-python-headless  (lightweight, no GUI)

    TODO: Implement when deploying on the Pi.
    """

    # Recommended resolutions for Pi Zero W (low CPU)
    RES_LOW = (320, 240)       # Fast, minimal CPU
    RES_MEDIUM = (640, 480)    # Balanced
    RES_HIGH = (1280, 720)     # Stills only — too slow for real-time

    def __init__(self, width: int = 640, height: int = 480,
                 source: str = "csi"):
        self.width = width
        self.height = height
        self.source = source    # "csi" (Pi camera) or "usb"
        self._device = None

    def init(self) -> None:
        raise NotImplementedError("Real camera driver not yet implemented.")

    def capture_image(self, filepath: str) -> str:
        raise NotImplementedError

    def capture_frame(self) -> bytes:
        raise NotImplementedError

    def get_resolution(self) -> tuple:
        return (self.width, self.height)

    def set_resolution(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def is_available(self) -> bool:
        raise NotImplementedError

    def cleanup(self) -> None:
        raise NotImplementedError
