"""
tests.test_platform — Platform Detection Tests
================================================
Verifies that the platform detection utility correctly identifies
the current OS (will return WINDOWS on dev machines).
"""

from utils.platform_detect import detect_platform, Platform


def test_detect_returns_valid_platform():
    """detect_platform() should return a valid Platform enum member."""
    platform = detect_platform()
    assert isinstance(platform, Platform)
    assert platform in Platform


def test_detect_on_windows():
    """On a Windows dev machine, detection should return WINDOWS."""
    import sys
    if sys.platform == "win32":
        assert detect_platform() == Platform.WINDOWS
