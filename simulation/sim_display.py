"""
simulation.sim_display — Simulated Display
=============================================
Replaces the real OLED/e-ink display on Windows for development.
Renders display output to the terminal (text mode) or optionally
opens a Tkinter/Pygame preview window.

Implements hardware.display.BaseDisplay interface.
"""

import logging
from hardware.display import BaseDisplay

logger = logging.getLogger(__name__)


class SimDisplay(BaseDisplay):
    """
    Simulated display for Windows development.

    Prints display content to the console.  A future enhancement
    could open a small Tkinter window to preview the OLED layout.
    """

    def __init__(self, width: int = 128, height: int = 64):
        self.width = width
        self.height = height
        self._is_sleeping = False
        self._brightness = 255
        logger.info(f"SimDisplay initialised ({width}×{height}).")

    def init(self) -> None:
        logger.info("SimDisplay: display ready.")

    def clear(self) -> None:
        logger.info("SimDisplay: screen cleared.")

    def show_text(self, text: str, x: int = 0, y: int = 0,
                  font_size: int = 12) -> None:
        logger.info(f"📺 DISPLAY [{x},{y}] \"{text}\"")

    def show_status(self, status: str) -> None:
        logger.info(f"📺 DISPLAY STATUS → {status}")

    def show_battery(self, percentage: int) -> None:
        bar = "█" * (percentage // 10) + "░" * (10 - percentage // 10)
        logger.info(f"🔋 DISPLAY BATTERY [{bar}] {percentage}%")

    def brightness(self, level: int) -> None:
        self._brightness = max(0, min(255, level))
        logger.info(f"SimDisplay: brightness set to {self._brightness}/255.")

    def sleep(self) -> None:
        self._is_sleeping = True
        logger.info("SimDisplay: entering sleep mode.")

    def wake(self) -> None:
        self._is_sleeping = False
        logger.info("SimDisplay: waking up.")

    def cleanup(self) -> None:
        logger.info("SimDisplay: cleaned up.")
