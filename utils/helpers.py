"""
utils.helpers — Miscellaneous Helpers
=======================================
Small utility functions shared across modules.
"""

import logging
import sys

logger = logging.getLogger(__name__)


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a value between low and high."""
    return max(low, min(high, value))


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, adding '…' if trimmed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def get_memory_usage_mb() -> float:
    """
    Return the current process memory usage in MB.
    Works on Linux (Pi). Falls back to 0 on Windows.
    """
    try:
        if sys.platform == "linux":
            import resource
            # ru_maxrss is in KB on Linux
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except (ImportError, OSError, AttributeError) as error:
        logger.warning("Could not read process memory usage: %s", error)
    return 0.0
