"""
hardware.button — GPIO Push-Button Driver
===========================================
Reads a physical push-button connected to a GPIO pin on the Pi.
Used as the "talk" trigger — press-and-hold to speak, release to process.

Uses RPi.GPIO or gpiozero (Pi only).
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class BaseButton(ABC):
    """Interface for the physical button."""

    @abstractmethod
    def is_pressed(self) -> bool:
        """Return True if the button is currently held down."""
        ...

    @abstractmethod
    def on_press(self, callback: Callable) -> None:
        """Register a callback for button-press events."""
        ...

    @abstractmethod
    def on_release(self, callback: Callable) -> None:
        """Register a callback for button-release events."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release GPIO resources."""
        ...


class Button(BaseButton):
    """
    Real GPIO button driver for Raspberry Pi.

    TODO: Implement with RPi.GPIO when deploying on the Pi.
    """

    def __init__(self, gpio_pin: int = 17):
        self.gpio_pin = gpio_pin
        self._press_cb: Optional[Callable] = None
        self._release_cb: Optional[Callable] = None

    def is_pressed(self) -> bool:
        raise NotImplementedError("Real button driver not yet implemented.")

    def on_press(self, callback: Callable) -> None:
        self._press_cb = callback

    def on_release(self, callback: Callable) -> None:
        self._release_cb = callback

    def cleanup(self) -> None:
        raise NotImplementedError
