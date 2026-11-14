"""
hardware.camera — Camera Interface & Pi Implementation
========================================================
Defines the CameraInterface ABC and the PiCamera driver.

The camera is fully OPTIONAL and never activates automatically.
It provides an interface for future image-capture features
(e.g., QR scanning, scene description via vision LLM).

Pi-specific dependencies (lazy-imported):
  - picamera2   (official Raspberry Pi camera library)
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ── Interface ──────────────────────────────────────────────────

class CameraInterface(ABC):
    """
    Abstract camera interface.

    The camera is optional — the system must work without one.
    Implementations must NOT activate the camera on __init__;
    only capture_image() triggers the hardware.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if a camera is detected and usable."""
        ...

    @abstractmethod
    def capture_image(self, filepath: str) -> str:
        """
        Capture a single still image and save it.

        This is the ONLY method that activates the camera hardware.

        Parameters
        ----------
        filepath : str
            Destination file path for the image.

        Returns
        -------
        str
            The path to the saved image, or empty string on failure.
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release camera resources."""
        ...


# ── Raspberry Pi Implementation ───────────────────────────────

class PiCamera(CameraInterface):
    """
    Real camera driver for Raspberry Pi Camera Module (CSI).

    The camera is NOT activated during __init__.  It is only
    powered on when capture_image() is called, and powered off
    immediately after capture to save power and RAM.

    Parameters
    ----------
    width : int
        Capture width (default 640 — low res for Pi Zero W).
    height : int
        Capture height (default 480).
    """

    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self._camera = None  # Never opened in __init__

    def is_available(self) -> bool:
        """Check if picamera2 is importable and a camera is present."""
        try:
            from picamera2 import Picamera2
            cam = Picamera2()
            cam.close()
            return True
        except Exception:
            return False

    def capture_image(self, filepath: str) -> str:
        cam = None
        started = False
        try:
            from picamera2 import Picamera2

            cam = Picamera2()
            config = cam.create_still_configuration(
                main={"size": (self.width, self.height)}
            )
            cam.configure(config)
            cam.start()
            started = True
            cam.capture_file(filepath)
            logger.info(f"PiCamera: image saved to {filepath}")
            return filepath
        except ImportError:
            logger.error("PiCamera: picamera2 not installed.")
            return ""
        except Exception as e:
            logger.error(f"PiCamera capture failed: {e}")
            return ""
        finally:
            if cam is not None:
                if started:
                    try:
                        cam.stop()
                    except Exception:
                        logger.warning("PiCamera stop failed during cleanup.", exc_info=True)
                try:
                    cam.close()
                except Exception:
                    logger.warning("PiCamera close failed during cleanup.", exc_info=True)

    def cleanup(self) -> None:
        # No persistent resources — camera is opened/closed per capture
        logger.info("PiCamera: cleaned up.")
