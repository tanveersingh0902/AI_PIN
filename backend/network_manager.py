"""Read-only network status and bounded connectivity checks."""

from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from network.wifi import WiFiManager

logger = logging.getLogger(__name__)


class WiFiStatusProvider(Protocol):
    def is_wifi_connected(self) -> bool | None:
        """Return Wi-Fi association status, or None when unknown."""


@dataclass(frozen=True)
class NetworkStatus:
    wifi_connected: bool | None
    internet_available: bool
    groq_configured: bool
    checked_at: datetime | None
    last_successful_check: datetime | None
    last_error: str | None


class NetworkManager:
    """Checks Wi-Fi association separately from internet reachability."""

    def __init__(
        self,
        api_key: str = "",
        wifi_manager: WiFiStatusProvider | None = None,
        connectivity_check_timeout: float = 2.0,
        connection_timeout: float = 15.0,
        internet_probe: Callable[[float], bool] | None = None,
    ):
        self._groq_configured = bool(api_key)
        self._wifi_manager = wifi_manager or WiFiManager()
        self._check_timeout = max(0.1, connectivity_check_timeout)
        self._connection_timeout = max(0.0, connection_timeout)
        self._internet_probe = (
            internet_probe if internet_probe is not None else self._probe_internet
        )
        self._probe_error: OSError | None = None
        self._status = NetworkStatus(
            wifi_connected=None,
            internet_available=False,
            groq_configured=self._groq_configured,
            checked_at=None,
            last_successful_check=None,
            last_error=None,
        )

    @property
    def status(self) -> NetworkStatus:
        return self._status

    def check_status(
        self, probe_timeout: float | None = None
    ) -> NetworkStatus:
        """Perform one Wi-Fi and internet check, recording the result."""
        previous = self._status
        try:
            wifi_connected = self._wifi_manager.is_wifi_connected()
        except OSError:
            wifi_connected = None

        checked_at = datetime.now(timezone.utc)
        self._probe_error = None
        timeout = self._check_timeout
        if probe_timeout is not None:
            timeout = min(timeout, max(0.01, probe_timeout))
        try:
            internet_available = bool(self._internet_probe(timeout))
            last_error = None if internet_available else "Internet probe failed."
            if self._probe_error is not None:
                last_error = (
                    f"{type(self._probe_error).__name__}: {self._probe_error}"
                )
        except OSError as error:
            internet_available = False
            last_error = f"{type(error).__name__}: {error}"

        last_success = (
            checked_at if internet_available else previous.last_successful_check
        )
        current = NetworkStatus(
            wifi_connected=wifi_connected,
            internet_available=internet_available,
            groq_configured=self._groq_configured,
            checked_at=checked_at,
            last_successful_check=last_success,
            last_error=last_error,
        )
        if previous.wifi_connected != current.wifi_connected:
            logger.info("Wi-Fi association: %s", self._wifi_label(wifi_connected))
        if previous.internet_available != current.internet_available:
            label = "available" if internet_available else "unavailable"
            logger.info("Internet connectivity is %s.", label)
        self._status = current
        return current

    def is_internet_available(self) -> bool:
        """Return current internet status after a fresh lightweight check."""
        return self.check_status().internet_available

    def wait_for_connectivity(
        self, timeout: float | None = None, poll_interval: float = 1.0
    ) -> bool:
        """Wait for internet recovery, checking at a controlled interval."""
        total_timeout = (
            self._connection_timeout if timeout is None else max(0.0, timeout)
        )
        interval = max(0.1, poll_interval)
        deadline = time.monotonic() + total_timeout

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            if self.check_status(probe_timeout=remaining).internet_available:
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(interval, remaining))

    def diagnostics(self, refresh: bool = True) -> str:
        """Return a readable status report without exposing credentials."""
        status = self.check_status() if refresh else self._status
        checked = status.checked_at.isoformat() if status.checked_at else "never"
        last_success = (
            status.last_successful_check.isoformat()
            if status.last_successful_check
            else "never"
        )
        error = status.last_error or "none"
        return "\n".join(
            (
                f"Wi-Fi: {self._wifi_label(status.wifi_connected)}",
                "Internet: "
                + ("available" if status.internet_available else "unavailable"),
                "Groq API key: "
                + ("configured" if status.groq_configured else "missing"),
                f"Last check: {checked}",
                f"Last successful internet check: {last_success}",
                f"Current network error: {error}",
            )
        )

    def _probe_internet(self, timeout: float) -> bool:
        try:
            with socket.create_connection(("1.1.1.1", 443), timeout=timeout):
                return True
        except OSError as error:
            self._probe_error = error
            return False

    @staticmethod
    def _wifi_label(connected: bool | None) -> str:
        if connected is None:
            return "unknown"
        return "connected" if connected else "disconnected"
