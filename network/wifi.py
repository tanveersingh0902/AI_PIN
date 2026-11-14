"""Read-only Wi-Fi association detection for Windows and Linux."""

from __future__ import annotations

import re
import logging
import platform
import socket
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class WiFiManager:
    """Wi-Fi connectivity helper."""

    def __init__(self, command_timeout: float = 2.0):
        self.command_timeout = command_timeout

    def is_connected(self) -> bool:
        """
        Check if the device has internet access.

        Kept for compatibility; Wi-Fi association is checked separately.
        """
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=3):
                pass
            return True
        except OSError:
            return False

    def is_wifi_connected(self) -> bool | None:
        """Return Wi-Fi association status, or None when it is undetectable."""
        system = platform.system().lower()
        if system == "windows":
            result = self._run(["netsh", "wlan", "show", "interfaces"])
            if result is None or result.returncode != 0:
                return None
            match = re.search(
                r"^\s*State\s*:\s*(.+?)\s*$",
                result.stdout,
                re.IGNORECASE | re.MULTILINE,
            )
            if match is None:
                return None
            return match.group(1).strip().lower() == "connected"

        if system == "linux":
            result = self._run(["iwgetid", "-r"])
            if result is not None and result.returncode == 0:
                return bool(result.stdout.strip())

            result = self._run(["iw", "dev", "wlan0", "link"])
            if result is not None and result.returncode == 0:
                output = result.stdout.lower()
                if "not connected" in output:
                    return False
                if "connected to " in output:
                    return True

            return self._linux_sysfs_status()

        return None

    def _run(self, command: list[str]):
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def _linux_sysfs_status() -> bool | None:
        interfaces = Path("/sys/class/net")
        try:
            carriers = [
                (interface / "carrier").read_text().strip()
                for interface in interfaces.glob("wl*/carrier")
            ]
        except OSError:
            return None
        if not carriers:
            return None
        return any(carrier == "1" for carrier in carriers)

    def get_ssid(self) -> str:
        """
        Return the name of the currently connected Wi-Fi network.

        SSID reporting is intentionally not implemented; diagnostics do not
        need to expose network names.
        """
        logger.warning("WiFiManager.get_ssid() is intentionally unsupported.")
        return ""

    def connect(self, ssid: str, password: str) -> bool:
        """
        Wi-Fi configuration is managed by the operating system, not this app.

        This compatibility method intentionally does not change network
        settings or retain credentials.
        """
        del ssid, password
        logger.warning("WiFiManager.connect() is intentionally unsupported.")
        return False
