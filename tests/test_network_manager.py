"""Offline tests for connectivity checks and bounded Groq retries."""

from types import SimpleNamespace

import pytest

from backend.network_manager import NetworkManager
from network.retry import call_with_retries, error_summary
from network.wifi import WiFiManager


class FakeWiFi:
    def __init__(self, connected):
        self.connected = connected

    def is_wifi_connected(self):
        return self.connected


def test_wifi_and_internet_status_are_reported_separately():
    manager = NetworkManager(
        api_key="never-display-this",
        wifi_manager=FakeWiFi(True),
        internet_probe=lambda _timeout: False,
    )

    status = manager.check_status()
    report = manager.diagnostics(refresh=False)

    assert status.wifi_connected is True
    assert status.internet_available is False
    assert status.last_error == "Internet probe failed."
    assert "Wi-Fi: connected" in report
    assert "Internet: unavailable" in report
    assert "Groq API key: configured" in report
    assert "never-display-this" not in report


def test_internet_available_updates_last_successful_check():
    manager = NetworkManager(
        wifi_manager=FakeWiFi(False),
        internet_probe=lambda _timeout: True,
    )

    status = manager.check_status()

    assert status.wifi_connected is False
    assert status.internet_available is True
    assert status.last_error is None
    assert status.last_successful_check == status.checked_at


def test_failed_check_preserves_last_successful_check():
    results = iter([True, False])
    manager = NetworkManager(
        internet_probe=lambda _timeout: next(results),
    )

    first = manager.check_status()
    second = manager.check_status()

    assert second.internet_available is False
    assert second.last_successful_check == first.checked_at


def test_connectivity_timeout_and_recovery(monkeypatch):
    results = iter([False, False, True])
    manager = NetworkManager(
        connection_timeout=1,
        internet_probe=lambda _timeout: next(results),
    )
    monkeypatch.setattr("backend.network_manager.time.sleep", lambda _delay: None)

    assert manager.wait_for_connectivity(timeout=1, poll_interval=0.1)


def test_connectivity_timeout_returns_false(monkeypatch):
    manager = NetworkManager(
        internet_probe=lambda _timeout: False,
    )
    monkeypatch.setattr("backend.network_manager.time.sleep", lambda _delay: None)

    assert not manager.wait_for_connectivity(timeout=0)


def test_socket_probe_reports_timeout_details(monkeypatch):
    def fail_connect(*_args, **_kwargs):
        raise TimeoutError("probe timeout")

    monkeypatch.setattr("backend.network_manager.socket.create_connection", fail_connect)
    manager = NetworkManager()

    status = manager.check_status()

    assert not status.internet_available
    assert status.last_error == "TimeoutError: probe timeout"


def test_windows_wifi_detection_parses_association_without_ssid(monkeypatch):
    monkeypatch.setattr("network.wifi.platform.system", lambda: "Windows")
    manager = WiFiManager()
    monkeypatch.setattr(
        manager,
        "_run",
        lambda _command: SimpleNamespace(
            returncode=0, stdout="State : connected\nSSID : private-network"
        ),
    )

    assert manager.is_wifi_connected() is True


def test_linux_wifi_detection_handles_missing_commands(monkeypatch):
    monkeypatch.setattr("network.wifi.platform.system", lambda: "Linux")
    manager = WiFiManager()
    monkeypatch.setattr(manager, "_run", lambda _command: None)
    monkeypatch.setattr(manager, "_linux_sysfs_status", lambda: None)

    assert manager.is_wifi_connected() is None


class HttpError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


def test_retry_uses_exponential_backoff(monkeypatch):
    sleeps = []
    attempts = []
    monkeypatch.setattr("network.retry.time.sleep", sleeps.append)

    def request():
        attempts.append(None)
        if len(attempts) < 3:
            raise HttpError(503)
        return "ok"

    assert call_with_retries(
        request, retry_count=2, retry_delay=0.25, operation_name="test"
    ) == "ok"
    assert len(attempts) == 3
    assert sleeps == [0.25, 0.5]


@pytest.mark.parametrize("status_code", [401, 403])
def test_authentication_failures_are_not_retried(monkeypatch, status_code):
    sleeps = []
    attempts = []
    monkeypatch.setattr("network.retry.time.sleep", sleeps.append)

    def request():
        attempts.append(None)
        raise HttpError(status_code)

    with pytest.raises(HttpError):
        call_with_retries(request, retry_count=4)

    assert len(attempts) == 1
    assert sleeps == []
    assert error_summary(HttpError(status_code)) == (
        f"authentication failed (HTTP {status_code})"
    )


def test_rate_limit_is_retryable_and_error_is_sanitized(monkeypatch):
    monkeypatch.setattr("network.retry.time.sleep", lambda _delay: None)
    attempts = []

    def request():
        attempts.append(None)
        if len(attempts) == 1:
            raise HttpError(429)
        return "ok"

    assert call_with_retries(request, retry_count=1) == "ok"
    assert len(attempts) == 2
    assert error_summary(HttpError(429)) == "rate limited (HTTP 429)"


def test_request_timeout_is_retryable(monkeypatch):
    monkeypatch.setattr("network.retry.time.sleep", lambda _delay: None)
    attempts = []

    def request():
        attempts.append(None)
        if len(attempts) == 1:
            raise TimeoutError("private request details")
        return "ok"

    assert call_with_retries(request, retry_count=1) == "ok"
    assert len(attempts) == 2


def test_retry_limit_is_capped(monkeypatch):
    monkeypatch.setattr("network.retry.time.sleep", lambda _delay: None)
    attempts = []

    def request():
        attempts.append(None)
        raise HttpError(503)

    with pytest.raises(HttpError):
        call_with_retries(request, retry_count=100)

    assert len(attempts) == 6
