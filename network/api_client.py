"""Generic requests wrapper retained for non-Groq HTTP integrations.

The VIHAAN assistant uses the Groq SDK directly with bounded retries
from network.retry.
"""

from __future__ import annotations

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
    logger.debug("GET request")
    return get_session().get(url, params=params, timeout=timeout, **kwargs)


def api_post(url: str, json: dict | None = None,
             timeout: int = DEFAULT_TIMEOUT, **kwargs: Any) -> requests.Response:
    """POST with timeout and logging."""
    logger.debug("POST request")
    return get_session().post(url, json=json, timeout=timeout, **kwargs)
