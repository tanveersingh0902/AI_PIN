"""
utils.platform_detect — Runtime Platform Detection
====================================================
Determines whether the code is running on:
  - Windows (development machine)
  - Raspberry Pi (production target)
  - Linux (other — e.g., CI server)

This lets the rest of the codebase branch between real and simulated
hardware without hard-coding platform checks everywhere.
"""

import platform
from enum import Enum


class Platform(Enum):
    WINDOWS = "windows"
    RASPBERRY_PI = "raspberry_pi"
    LINUX = "linux"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    """
    Detect the current runtime platform.

    Returns
    -------
    Platform
        The detected platform enum value.
    """
    system = platform.system().lower()

    if system == "windows":
        return Platform.WINDOWS

    if system == "linux":
        # Check for Raspberry Pi by inspecting /proc/cpuinfo
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read().lower()
            if "raspberry" in cpuinfo or "bcm" in cpuinfo:
                return Platform.RASPBERRY_PI
        except FileNotFoundError:
            pass

        # Fallback: check the machine architecture
        machine = platform.machine().lower()
        if machine in ("armv6l", "armv7l", "aarch64"):
            # Likely a Pi or similar ARM SBC
            return Platform.RASPBERRY_PI

        return Platform.LINUX

    return Platform.UNKNOWN


def is_raspberry_pi() -> bool:
    """Convenience check: are we on a Raspberry Pi?"""
    return detect_platform() == Platform.RASPBERRY_PI
