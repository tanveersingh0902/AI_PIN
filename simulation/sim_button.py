"""
simulation.sim_button — Simulated Button
==========================================
Replaces the GPIO button on Windows for development.
Listens for a keyboard key press (e.g., spacebar) instead of a
physical button.

Implements hardware.button.BaseButton interface.
"""

import logging
from typing import Callable, Optional
from hardware.button import BaseButton

logger = logging.getLogger(__name__)


class SimButton(BaseButton):
    """
    Simulated push-button using keyboard input.

    TODO: Implement with a keyboard listener (e.g., `keyboard` library
          or `input()` prompt) for interactive dev testing.
    """

    def __init__(self):
        self._pressed = False
        self._press_cb: Optional[Callable] = None
        self._release_cb: Optional[Callable] = None
        logger.info("SimButton initialised (use keyboard to simulate).")

    def is_pressed(self) -> bool:
        return self._pressed

    def on_press(self, callback: Callable) -> None:
        self._press_cb = callback
        logger.info("SimButton: press callback registered.")

    def on_release(self, callback: Callable) -> None:
        self._release_cb = callback
        logger.info("SimButton: release callback registered.")

    def simulate_press(self) -> None:
        """Call this from a keyboard listener or test."""
        self._pressed = True
        if self._press_cb:
            self._press_cb()

    def simulate_release(self) -> None:
        """Call this from a keyboard listener or test."""
        self._pressed = False
        if self._release_cb:
            self._release_cb()

    def cleanup(self) -> None:
        logger.info("SimButton: cleaned up.")
