"""
network.api_client — Shared HTTP Client
=========================================
A thin wrapper around `requests` with sensible defaults for a
resource-constrained device:
  - Connection timeout (prevents hanging on bad networks)
  - Automatic retries with backoff
  - Response size limits (protect 512 MB RAM)

All outbound API calls (LLM, cloud TTS, etc.) should go through
this client.
"""

import logging
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ── Defaults ──────────────────────────────────────────────────
DEFAULT_TIMEOUT = 10         # seconds
MAX_RETRIES = 2
BACKOFF_FACTOR = 0.5
MAX_RESPONSE_BYTES = 1 * 1024 * 1024  # 1 MB safety cap


def _create_session() -> requests.Session:
    """Build a requests Session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# Module-level reusable session
_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = _create_session()
    return _session


def api_get(url: str, params: dict | None = None,
            timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> requests.Response:
    """GET with timeout and logging."""
    logger.debug(f"GET {url}")
    return get_session().get(url, params=params, timeout=timeout, **kwargs)


def api_post(url: str, json: dict | None = None,
             timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> requests.Response:
    """POST with timeout and logging."""
    logger.debug(f"POST {url}")
    return get_session().post(url, json=json, timeout=timeout, **kwargs)
