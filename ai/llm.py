"""
ai.llm — Groq LLM Client
===========================
Sends user queries to Groq's chat completion API and returns
the assistant's response.

Model: openai/gpt-oss-120b (cloud-based, via Groq infrastructure).

Dependencies:
  - groq (official Groq Python SDK)
"""

from __future__ import annotations

import logging
from typing import Optional

from network.retry import call_with_retries, error_summary

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Groq-powered LLM client for VIHAAN AI PIN.

    Parameters
    ----------
    api_key : str
        Groq API key (from env, never hardcoded).
    model : str
        Model identifier on Groq.
    max_tokens : int
        Maximum response tokens (kept small for voice output).
    temperature : float
        Sampling temperature (0.0–2.0).
    timeout : float
        HTTP request timeout in seconds.
    system_prompt : str or None
        Custom system prompt.  Falls back to DEFAULT_SYSTEM_PROMPT.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are VIHAAN, a helpful and concise voice assistant running on "
        "a wearable AI pin. Keep responses short (1–3 sentences) and "
        "spoken-language friendly. Avoid markdown, code blocks, or long "
        "lists. Be warm, direct, and useful."
    )

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b",
                 max_tokens: int = 256, temperature: float = 0.7,
                 timeout: float = 30.0,
                 system_prompt: Optional[str] = None,
                 retry_count: int = 2, retry_delay: float = 0.5):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for the LLM.")
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout
        self._system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self._retry_count = max(0, retry_count)
        self._retry_delay = max(0.0, retry_delay)
        self._client = None  # lazy init
        self.last_error: str | None = None
        logger.info(f"LLMClient: model={model}, max_tokens={max_tokens}")

    # ── Lazy client ───────────────────────────────────────────

    def _ensure_client(self):
        """Create the Groq client on first use (not on import)."""
        if self._client is None:
            from groq import Groq
            self._client = Groq(
                api_key=self._api_key,
                timeout=self._timeout,
                max_retries=0,
            )

    # ── Public API ────────────────────────────────────────────

    def query(self, user_message: str,
              conversation_history: list[dict] | None = None) -> str:
        """
        Send a message to the LLM and return the text response.

        Parameters
        ----------
        user_message : str
            What the user said (transcribed speech).
        conversation_history : list of dict, optional
            Prior turns as [{"role": "user"|"assistant", "content": "…"}, …].
            The system prompt is prepended automatically.

        Returns
        -------
        str
            The assistant's reply, or empty string on failure.
        """
        if not user_message or not user_message.strip():
            logger.warning("LLM: empty user message, skipping.")
            return ""

        try:
            self._ensure_client()

            messages = [{"role": "system", "content": self._system_prompt}]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_message})

            def request() -> str:
                completion = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                )
                return completion.choices[0].message.content.strip()

            response = call_with_retries(
                request,
                retry_count=self._retry_count,
                retry_delay=self._retry_delay,
                operation_name="Groq LLM request",
            )
            self.last_error = None
            logger.info("LLM response received (%d characters).", len(response))
            return response

        except Exception as error:
            self.last_error = error_summary(error)
            logger.error("LLM request failed: %s", self.last_error)
            return ""
