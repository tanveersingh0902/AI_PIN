"""
hardware.display — Display Driver
====================================
Controls a small display attached to the VIHAAN AI PIN.
Supports OLED (SSD1306 / SH1106) or e-ink displays connected
via I2C or SPI to the Raspberry Pi.

Used to show:
  - Device status (listening, thinking, speaking)
  - Transcribed text / assistant response
  - Battery level, Wi-Fi signal
  - Time / notifications

On the Pi this uses lightweight libraries like `luma.oled` or
`Pillow` for rendering.  On Windows the simulation layer
substitutes this module.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseDisplay(ABC):
    """Interface that both real and simulated displays implement."""

    @abstractmethod
    def init(self) -> None:
        """Initialise the display hardware / connection."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear the screen."""
        ...

    @abstractmethod
    def show_text(self, text: str, x: int = 0, y: int = 0,
                  font_size: int = 12) -> None:
        """Render a text string at the given position."""
        ...

    @abstractmethod
    def show_status(self, status: str) -> None:
        """Show a device status label (e.g., 'Listening…')."""
        ...

    @abstractmethod
    def show_battery(self, percentage: int) -> None:
        """Show battery level indicator."""
        ...

    @abstractmethod
    def brightness(self, level: int) -> None:
        """Set display brightness (0–255)."""
        ...

    @abstractmethod
    def sleep(self) -> None:
        """Put the display into low-power sleep mode."""
        ...

    @abstractmethod
    def wake(self) -> None:
        """Wake the display from sleep mode."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release display resources."""
        ...


class Display(BaseDisplay):
    """
    Real display driver for Raspberry Pi.

    Targets:
      - SSD1306 128×64 OLED (I2C) — most common, ~\$3
      - SH1106  128×64 OLED (I2C/SPI)
      - Waveshare e-ink (SPI) — for ultra-low-power use

    Dependencies (Pi only):
      - luma.oled  (for OLED)
      - luma.core  (rendering framework)
      - Pillow     (image/text rendering)

    TODO: Implement when deploying on the Pi.
    """

    # Common OLED resolutions
    OLED_128x64 = (128, 64)
    OLED_128x32 = (128, 32)

    def __init__(self, width: int = 128, height: int = 64,
                 interface: str = "i2c", i2c_address: int = 0x3C):
        self.width = width
        self.height = height
        self.interface = interface      # "i2c" or "spi"
        self.i2c_address = i2c_address
        self._device = None
        self._is_sleeping = False

    def init(self) -> None:
        raise NotImplementedError("Real display driver not yet implemented.")

    def clear(self) -> None:
        raise NotImplementedError

    def show_text(self, text: str, x: int = 0, y: int = 0,
                  font_size: int = 12) -> None:
        raise NotImplementedError

    def show_status(self, status: str) -> None:
        raise NotImplementedError

    def show_battery(self, percentage: int) -> None:
        raise NotImplementedError

    def brightness(self, level: int) -> None:
        raise NotImplementedError

    def sleep(self) -> None:
        raise NotImplementedError

    def wake(self) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        raise NotImplementedError
