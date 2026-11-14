"""
ai.conversation — Conversation History Manager
================================================
Maintains the conversation history between the user and the
VIHAAN assistant in memory.

Designed to work with Groq's chat completion API message format:
  [{"role": "user"|"assistant", "content": "…"}, …]

History is capped to avoid excessive token usage and to stay
within the Pi Zero W's 512 MB RAM constraint.

This module is independent of hardware.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages multi-turn conversation history for the LLM.

    Parameters
    ----------
    system_prompt : str
        The system prompt prepended to every API call.
    max_turns : int
        Maximum number of user–assistant turn pairs to keep.
        Older turns are discarded to save tokens and RAM.
    """

    def __init__(self, system_prompt: str, max_turns: int = 10):
        self._system_prompt = system_prompt
        self._max_turns = max_turns
        self._history: list[dict[str, str]] = []
        logger.info(f"ConversationManager created (max {max_turns} turns).")

    # ── Properties ────────────────────────────────────────────

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self._system_prompt = value

    @property
    def turn_count(self) -> int:
        """Number of messages currently stored (user + assistant)."""
        return len(self._history)

    # ── Add messages ──────────────────────────────────────────

    def add_user_message(self, text: str) -> None:
        """Append a user message to history."""
        self._history.append({"role": "user", "content": text})
        self._trim()

    def add_assistant_message(self, text: str) -> None:
        """Append an assistant response to history."""
        self._history.append({"role": "assistant", "content": text})
        self._trim()

    # ── Retrieve ──────────────────────────────────────────────

    def get_messages(self) -> list[dict[str, str]]:
        """
        Return the full messages list ready for the LLM API.

        Returns a list starting with the system prompt, followed
        by the conversation history.  This is the exact format
        Groq's chat.completions.create() expects.
        """
        return [
            {"role": "system", "content": self._system_prompt},
            *self._history,
        ]

    def get_history(self) -> list[dict[str, str]]:
        """Return only the user/assistant turns (no system prompt)."""
        return list(self._history)

    # ── Control ───────────────────────────────────────────────

    def clear(self) -> None:
        """Clear all conversation history."""
        self._history.clear()
        logger.info("Conversation history cleared.")

    # ── Internal ──────────────────────────────────────────────

    def _trim(self) -> None:
        """Discard oldest messages if we exceed the cap."""
        max_messages = self._max_turns * 2  # Each turn = user + assistant
        if len(self._history) > max_messages:
            excess = len(self._history) - max_messages
            self._history = self._history[excess:]
            logger.debug(
                f"Conversation trimmed: dropped {excess} oldest message(s)."
            )
