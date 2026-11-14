"""Small retry helper for transient Groq API failures."""

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
MAX_RETRY_COUNT = 5
MAX_RETRY_DELAY = 30.0


def is_retryable_error(error: Exception) -> bool:
    """Retry transient transport, throttling, and server-side failures only."""
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return status_code in (408, 409, 429) or 500 <= status_code <= 599

    error_name = type(error).__name__.lower()
    return isinstance(error, (TimeoutError, ConnectionError)) or error_name in {
        "apiconnectionerror",
        "apitimeouterror",
    }


def error_summary(error: Exception) -> str:
    """Describe an API error without logging response bodies or credentials."""
    if isinstance(error, ModuleNotFoundError):
        dependency = error.name
        if dependency:
            return f"required dependency missing: {dependency}"
        return "required dependency missing"
    status_code = getattr(error, "status_code", None)
    if status_code == 401 or status_code == 403:
        return f"authentication failed (HTTP {status_code})"
    if status_code == 429:
        return "rate limited (HTTP 429)"
    if isinstance(status_code, int) and status_code >= 500:
        return f"Groq server error (HTTP {status_code})"
    if type(error).__name__.lower() in {"apitimeouterror", "timeoutexception"} or isinstance(
        error, TimeoutError
    ):
        return "request timed out"
    if type(error).__name__.lower() == "apiconnectionerror" or isinstance(
        error, ConnectionError
    ):
        return "connection failed"
    return type(error).__name__


def call_with_retries(
    operation: Callable[[], T],
    retry_count: int = 2,
    retry_delay: float = 0.5,
    operation_name: str = "API request",
) -> T:
    """Run an operation with bounded exponential backoff for transient errors."""
    retries = min(MAX_RETRY_COUNT, max(0, retry_count))
    base_delay = max(0.0, retry_delay)
    for attempt in range(retries + 1):
        try:
            return operation()
        except Exception as error:
            if attempt >= retries or not is_retryable_error(error):
                raise
            delay = min(base_delay * (2 ** attempt), MAX_RETRY_DELAY)
            logger.warning(
                "%s failed (%s); retrying in %.2f seconds (%d/%d).",
                operation_name,
                error_summary(error),
                delay,
                attempt + 1,
                retries,
            )
            time.sleep(delay)
    raise RuntimeError("Retry loop exited unexpectedly.")
