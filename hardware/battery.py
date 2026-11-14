"""
hardware.battery — Battery Monitor
====================================
Reads battery voltage through an ADC (e.g., MCP3008) connected via
SPI to the Raspberry Pi. Provides percentage estimation and low-battery
warnings.

Requires spidev (Pi only).
"""

from abc import ABC, abstractmethod


class BaseBattery(ABC):
    """Interface for battery monitoring."""

    @abstractmethod
    def voltage(self) -> float:
        """Return current battery voltage."""
        ...

    @abstractmethod
    def percentage(self) -> int:
        """Return estimated charge percentage (0–100)."""
        ...

    @abstractmethod
    def is_low(self) -> bool:
        """Return True if battery is critically low."""
        ...


class Battery(BaseBattery):
    """
    Real battery monitor for Raspberry Pi via SPI ADC.

    TODO: Implement with spidev when deploying on the Pi.
    """

    def __init__(self, adc_channel: int = 0, low_threshold: float = 3.3):
        self.adc_channel = adc_channel
        self.low_threshold = low_threshold

    def voltage(self) -> float:
        raise NotImplementedError("Real battery monitor not yet implemented.")

    def percentage(self) -> int:
        raise NotImplementedError

    def is_low(self) -> bool:
        raise NotImplementedError
