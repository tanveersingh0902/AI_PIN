"""
simulation.sim_button — Simulated Push-to-Talk Button
=======================================================
Drop-in replacement for PiButton on Windows / dev machines.

Provides three ways to trigger the button:
  1. Programmatic: call simulate_press() / simulate_release()
     (ideal for automated tests and pipeline integration).
  2. Interactive: wait_for_press() prompts via input() in the
     terminal — press Enter to simulate a button press.
  3. Keyboard: if the `keyboard` library is installed, listens
     for the spacebar as a push-to-talk key (optional).

Implements hardware.button.ButtonInterface.
"""

import logging
import threading
from typing import Callable, Optional

from hardware.button import ButtonInterface

logger = logging.getLogger(__name__)


class SimButton(ButtonInterface):
    """
    Simulated push-to-talk button for Windows development.

    No Raspberry Pi GPIO libraries required.
    """

    def __init__(self):
        self._pressed = False
        self._press_cb: Optional[Callable] = None
        self._release_cb: Optional[Callable] = None
        self._press_event = threading.Event()
        self._closed = threading.Event()
        self._input_thread: threading.Thread | None = None
        logger.info("SimButton: initialised (keyboard / programmatic trigger).")

    # ── Interface implementation ──────────────────────────────

    def is_pressed(self) -> bool:
        return self._pressed

    def on_press(self, callback: Callable[[], None]) -> None:
        self._press_cb = callback
        logger.info("SimButton: press callback registered.")

    def on_release(self, callback: Callable[[], None]) -> None:
        self._release_cb = callback
        logger.info("SimButton: release callback registered.")

    def wait_for_press(self, timeout: float | None = None) -> bool:
        """
        Block until the button is pressed.

        In interactive mode (terminal), prompts the user to press Enter.
        In test mode, waits for simulate_press() from another thread.
        """
        self._press_event.clear()

        if self._input_thread is None or not self._input_thread.is_alive():
            self._input_thread = threading.Thread(
                target=self._input_listener, daemon=True
            )
            self._input_thread.start()

        pressed = self._press_event.wait(timeout=timeout)
        if pressed:
            logger.info("SimButton: press detected.")
        else:
            logger.info("SimButton: wait timed out.")
        return pressed

    def _input_listener(self):
        """Use successive Enter presses to simulate press and release."""
        try:
            while not self._closed.is_set():
                input("  [SimButton] Press ENTER to start recording → ")
                self.simulate_press()
                input("  [SimButton] Press ENTER to stop recording → ")
                self.simulate_release()
        except (EOFError, OSError):
            # Not running in an interactive terminal (CI / pytest / test)
            pass

    # ── Programmatic triggers (for tests / pipeline) ──────────

    def simulate_press(self) -> None:
        """Simulate a button press event."""
        self._pressed = True
        self._press_event.set()
        logger.debug("SimButton: PRESSED (simulated)")
        if self._press_cb:
            self._press_cb()

    def simulate_release(self) -> None:
        """Simulate a button release event."""
        self._pressed = False
        self._press_event.clear()
        logger.debug("SimButton: RELEASED (simulated)")
        if self._release_cb:
            self._release_cb()

    # ── Cleanup ───────────────────────────────────────────────

    def cleanup(self) -> None:
        self._closed.set()
        self._pressed = False
        self._press_cb = None
        self._release_cb = None
        logger.info("SimButton: cleaned up.")
