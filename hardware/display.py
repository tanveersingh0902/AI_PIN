"""
hardware.display — Display Interface & Pi Implementation
==========================================================
Defines the DisplayInterface ABC and the PiDisplay driver for an
optional SPI TFT display (e.g., ST7735 1.8″ 128×160) on the
Raspberry Pi Zero W.

The display is entirely OPTIONAL.  If no display hardware is
present or the driver fails to initialise, the system continues
without it.

Status modes:
  IDLE, LISTENING, THINKING, SPEAKING, ERROR

Pi-specific dependencies (lazy-imported):
  - spidev, Pillow, or ST7735 library
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class DisplayStatus(Enum):
    """Standard device status labels shown on the display."""
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


# ── Interface ──────────────────────────────────────────────────

class DisplayInterface(ABC):
    """
    Abstract display interface.

    All display implementations (real and simulated) must implement
    this interface.  The display is always optional — the system
    must work without one.
    """

    @abstractmethod
    def init(self) -> None:
        """Initialise the display hardware / connection."""
        ...

    @abstractmethod
    def show_text(self, text: str, line: int = 0) -> None:
        """
        Display a line of text.

        Parameters
        ----------
        text : str
            Text to display.
        line : int
            Line number (0 = top).
        """
        ...

    @abstractmethod
    def show_status(self, status: DisplayStatus) -> None:
        """
        Show a device status indicator.

        Parameters
        ----------
        status : DisplayStatus
            One of IDLE, LISTENING, THINKING, SPEAKING, ERROR.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear the screen."""
        ...

    @abstractmethod
    def set_brightness(self, level: int) -> None:
        """
        Set display brightness (0–255).

        Parameters
        ----------
        level : int
            Brightness value, 0 = off, 255 = max.
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release display resources."""
        ...


# ── Raspberry Pi Implementation ───────────────────────────────

class PiDisplay(DisplayInterface):
    """
    Real display driver for an SPI TFT display on Raspberry Pi.

    Targets ST7735 128×160 or similar small SPI TFT displays.
    Uses the Pillow library to render text onto a framebuffer image
    and push it to the display via SPI.

    This is a STUB — the full rendering pipeline will be
    implemented when the display hardware is available.

    Parameters
    ----------
    width : int
        Display width in pixels (default 128).
    height : int
        Display height in pixels (default 160).
    spi_port : int
        SPI bus number (default 0).
    spi_cs : int
        SPI chip-select line (default 0).
    gpio_dc : int
        GPIO pin for data/command select (default 25).
    gpio_rst : int
        GPIO pin for reset (default 24).
    """

    # Status → short label mapping for small screens
    STATUS_LABELS = {
        DisplayStatus.IDLE:      "● READY",
        DisplayStatus.LISTENING: "🎤 LISTENING",
        DisplayStatus.THINKING:  "⏳ THINKING",
        DisplayStatus.SPEAKING:  "🔊 SPEAKING",
        DisplayStatus.ERROR:     "⚠ ERROR",
    }

    def __init__(self, width: int = 128, height: int = 160,
                 spi_port: int = 0, spi_cs: int = 0,
                 gpio_dc: int = 25, gpio_rst: int = 24):
        self.width = width
        self.height = height
        self.spi_port = spi_port
        self.spi_cs = spi_cs
        self.gpio_dc = gpio_dc
        self.gpio_rst = gpio_rst
        self._device = None
        self._current_status: DisplayStatus = DisplayStatus.IDLE

    def init(self) -> None:
        logger.info(
            f"PiDisplay: SPI TFT {self.width}×{self.height} "
            f"(SPI{self.spi_port}.{self.spi_cs}) — stub, not yet wired."
        )
        # TODO: Initialise SPI device and Pillow framebuffer
        # from ST7735 import ST7735
        # self._device = ST7735(port=self.spi_port, cs=self.spi_cs, ...)

    def show_text(self, text: str, line: int = 0) -> None:
        logger.info(f"PiDisplay [{line}]: {text}")
        # TODO: Render text onto framebuffer with Pillow and push to SPI

    def show_status(self, status: DisplayStatus) -> None:
        self._current_status = status
        label = self.STATUS_LABELS.get(status, status.value)
        logger.info(f"PiDisplay status: {label}")
        # TODO: Render centred status label on display

    def clear(self) -> None:
        logger.debug("PiDisplay: cleared.")
        # TODO: Fill framebuffer with black and push

    def set_brightness(self, level: int) -> None:
        level = max(0, min(255, level))
        logger.debug(f"PiDisplay: brightness → {level}")
        # TODO: PWM backlight control via GPIO

    def cleanup(self) -> None:
        if self._device:
            try:
                self.clear()
            except Exception:
                pass
        self._device = None
        logger.info("PiDisplay: cleaned up.")
