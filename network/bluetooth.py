"""
network.bluetooth — Bluetooth Manager
========================================
Manages Bluetooth connections for audio output (e.g., Bluetooth
earbuds/speaker) and potential data transfer.

This is a future module — Bluetooth audio on Pi Zero W requires
careful PulseAudio/BlueALSA configuration.

TODO: Implement when Bluetooth audio support is needed.
"""

import logging

logger = logging.getLogger(__name__)


class BluetoothManager:
    """Placeholder for Bluetooth connectivity."""

    def is_available(self) -> bool:
        """Check if Bluetooth hardware is available."""
        logger.warning("BluetoothManager not yet implemented.")
        return False

    def pair(self, device_address: str) -> bool:
        """Pair with a Bluetooth device."""
        logger.warning("BluetoothManager.pair() not yet implemented.")
        return False

    def disconnect(self) -> None:
        """Disconnect current Bluetooth device."""
        logger.warning("BluetoothManager.disconnect() not yet implemented.")
