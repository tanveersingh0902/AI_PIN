"""
hardware.button — Button Interface & Pi Implementation
========================================================
Defines the ButtonInterface ABC and the PiButton driver that reads
a physical push-to-talk button on GPIO17 of the Raspberry Pi.

Uses an internal pull-up resistor so the button connects GPIO17 to
GND when pressed.  Edge detection is interrupt-driven (non-blocking).

Pi-specific dependencies (lazy-imported):
  - RPi.GPIO
"""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from typing import Callable, Optional

logger = logging.getLogger(__name__)


# ── Interface ──────────────────────────────────────────────────

class ButtonInterface(ABC):
    """
    Abstract push-button interface.

    All button implementations (real and simulated) must implement
    this interface.
    """

    @abstractmethod
    def is_pressed(self) -> bool:
        """Return True if the button is currently held down."""
        ...

    @abstractmethod
    def on_press(self, callback: Callable[[], None]) -> None:
        """
        Register a callback that fires when the button is pressed.

        Parameters
        ----------
        callback : callable
            A zero-argument function to call on press.
        """
        ...

    @abstractmethod
    def on_release(self, callback: Callable[[], None]) -> None:
        """
        Register a callback that fires when the button is released.

        Parameters
        ----------
        callback : callable
            A zero-argument function to call on release.
        """
        ...

    @abstractmethod
    def wait_for_press(self, timeout: float | None = None) -> bool:
        """
        Block until the button is pressed or timeout expires.

        Parameters
        ----------
        timeout : float or None
            Max seconds to wait.  None = wait forever.

        Returns
        -------
        bool
            True if the button was pressed, False on timeout.
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware resources (GPIO, threads, etc.)."""
        ...


# ── Raspberry Pi Implementation ───────────────────────────────

class PiButton(ButtonInterface):
    """
    Real push-button driver using RPi.GPIO on the Raspberry Pi.

    Wiring: button connects GPIO pin to GND.  An internal pull-up
    resistor holds the pin HIGH when the button is not pressed.
    Pressing the button pulls the pin LOW.

    Edge detection is interrupt-based (no busy-loop polling).

    Parameters
    ----------
    gpio_pin : int
        BCM GPIO pin number (default 17).
    bounce_time_ms : int
        Software debounce time in milliseconds (default 200).
    """

    def __init__(self, gpio_pin: int = 17, bounce_time_ms: int = 200):
        self._gpio_pin = gpio_pin
        self._bounce_time_ms = bounce_time_ms
        self._press_cb: Optional[Callable] = None
        self._release_cb: Optional[Callable] = None
        self._press_event = threading.Event()
        self._gpio = None
        self._setup_done = False

    def _ensure_gpio(self):
        """Lazy-init RPi.GPIO (avoids import on Windows)."""
        if self._setup_done:
            return
        import RPi.GPIO as GPIO
        self._gpio = GPIO

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Register edge detection for both press (FALLING) and release (RISING)
        GPIO.add_event_detect(
            self._gpio_pin,
            GPIO.BOTH,
            callback=self._edge_callback,
            bouncetime=self._bounce_time_ms,
        )
        self._setup_done = True
        logger.info(f"PiButton: GPIO{self._gpio_pin} configured (pull-up, BOTH edges).")

    def _edge_callback(self, channel: int):
        """Called by RPi.GPIO on any edge change."""
        # Pull-up: LOW = pressed, HIGH = released
        pressed = self._gpio.input(self._gpio_pin) == self._gpio.LOW
        if pressed:
            logger.debug("PiButton: PRESSED")
            self._press_event.set()
            if self._press_cb:
                self._press_cb()
        else:
            logger.debug("PiButton: RELEASED")
            self._press_event.clear()
            if self._release_cb:
                self._release_cb()

    def is_pressed(self) -> bool:
        self._ensure_gpio()
        return self._gpio.input(self._gpio_pin) == self._gpio.LOW

    def on_press(self, callback: Callable[[], None]) -> None:
        self._ensure_gpio()
        self._press_cb = callback
        logger.info("PiButton: press callback registered.")

    def on_release(self, callback: Callable[[], None]) -> None:
        self._ensure_gpio()
        self._release_cb = callback
        logger.info("PiButton: release callback registered.")

    def wait_for_press(self, timeout: float | None = None) -> bool:
        self._ensure_gpio()
        self._press_event.clear()
        return self._press_event.wait(timeout=timeout)

    def cleanup(self) -> None:
        if self._gpio:
            try:
                if self._setup_done:
                    self._gpio.remove_event_detect(self._gpio_pin)
            except Exception as e:
                logger.warning("PiButton event cleanup warning: %s", e)
            try:
                self._gpio.cleanup(self._gpio_pin)
            except Exception as e:
                logger.warning("PiButton GPIO cleanup warning: %s", e)
        self._setup_done = False
        logger.info("PiButton: cleaned up.")
