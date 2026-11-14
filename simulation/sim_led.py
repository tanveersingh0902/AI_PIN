"""
simulation.sim_led — Simulated LED
====================================
Replaces the GPIO LED on Windows for development.
Prints LED state changes to the console with colour codes / emoji.

Implements hardware.led.BaseLED interface.
"""

from __future__ import annotations

import logging
import threading
from hardware.led import BaseLED

logger = logging.getLogger(__name__)


class SimLED(BaseLED):
    """
    Simulated status LED — outputs to the terminal.
    """

    def __init__(self, name: str = "STATUS"):
        self.name = name
        self._blinking = False
        self._blink_thread: threading.Thread | None = None
        logger.info(f"SimLED '{name}' initialised.")

    def on(self) -> None:
        self._blinking = False
        logger.info(f"💡 LED [{self.name}] ON")

    def off(self) -> None:
        self._blinking = False
        logger.info(f"⚫ LED [{self.name}] OFF")

    def blink(self, interval: float = 0.5) -> None:
        self._blinking = True
        logger.info(f"✨ LED [{self.name}] BLINKING (interval={interval}s)")
        # In a real implementation, spawn a thread to toggle on/off.

    def cleanup(self) -> None:
        self._blinking = False
        logger.info(f"SimLED '{self.name}' cleaned up.")
