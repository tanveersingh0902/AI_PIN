"""
hardware.led — Status LED Driver
==================================
Controls one or more LEDs connected to GPIO pins on the Pi.
Used to indicate device state: listening, thinking, error, etc.

Uses RPi.GPIO or gpiozero (Pi only).
"""

from abc import ABC, abstractmethod


class BaseLED(ABC):
    """Interface for status LED control."""

    @abstractmethod
    def on(self) -> None:
        """Turn the LED on (solid)."""
        ...

    @abstractmethod
    def off(self) -> None:
        """Turn the LED off."""
        ...

    @abstractmethod
    def blink(self, interval: float = 0.5) -> None:
        """Blink the LED at the given interval (seconds)."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release GPIO resources."""
        ...


class LED(BaseLED):
    """
    Real GPIO LED driver for Raspberry Pi.

    TODO: Implement with RPi.GPIO when deploying on the Pi.
    """

    def __init__(self, gpio_pin: int = 27):
        self.gpio_pin = gpio_pin

    def on(self) -> None:
        raise NotImplementedError("Real LED driver not yet implemented.")

    def off(self) -> None:
        raise NotImplementedError

    def blink(self, interval: float = 0.5) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        raise NotImplementedError
