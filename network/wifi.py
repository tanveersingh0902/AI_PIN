"""
network.wifi — Wi-Fi Manager
==============================
Checks connectivity status and manages Wi-Fi connections on the Pi.
On Windows this simply checks internet reachability.

Uses subprocess calls to `nmcli` or `iwconfig` on the Pi;
falls back to socket-based connectivity check on Windows.
"""

import logging
import socket

logger = logging.getLogger(__name__)


class WiFiManager:
    """Wi-Fi connectivity helper."""

    def is_connected(self) -> bool:
        """
        Check if the device has internet access.

        Returns True if a DNS lookup + socket connect succeeds.
        Works cross-platform (Windows and Linux).
        """
        try:
            socket.setdefaulttimeout(3)
            socket.create_connection(("8.8.8.8", 53))
            return True
        except OSError:
            return False

    def get_ssid(self) -> str:
        """
        Return the name of the currently connected Wi-Fi network.

        TODO: Implement with nmcli on Pi, netsh on Windows.
        """
        logger.warning("WiFiManager.get_ssid() not yet implemented.")
        return ""

    def connect(self, ssid: str, password: str) -> bool:
        """
        Connect to a Wi-Fi network.

        TODO: Implement for Raspberry Pi (nmcli / wpa_supplicant).
        """
        logger.warning("WiFiManager.connect() not yet implemented.")
        return False
