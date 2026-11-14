"""
backend.session — Conversation Session Manager
================================================
Manages short-term conversation history for the LLM so that
follow-up questions work naturally.

Keeps history in-memory with a hard cap on turns to stay within
the Pi Zero W's 512 MB RAM limit.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Maximum conversation turns to keep in memory
MAX_HISTORY_TURNS = 10


class Session:
    """
    A single conversation session.

    TODO: Add timestamp-based auto-expiry and optional persistence
          to a lightweight JSON file.
    """

    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self.max_turns = max_turns
        self._history: List[Dict[str, str]] = []
        logger.info(f"Session created (max {max_turns} turns).")

    def add_turn(self, role: str, content: str) -> None:
        """
        Add a user or assistant turn to history.

        Parameters
        ----------
        role : str
            "user" or "assistant"
        content : str
            The message text.
        """
        self._history.append({"role": role, "content": content})

        # Trim oldest turns if we exceed the cap
        if len(self._history) > self.max_turns * 2:
            self._history = self._history[-(self.max_turns * 2):]
            logger.debug("Session history trimmed to fit memory cap.")

    @property
    def history(self) -> List[Dict[str, str]]:
        """Return the current conversation history."""
        return list(self._history)

    def clear(self) -> None:
        """Reset the session."""
        self._history.clear()
        logger.info("Session cleared.")
