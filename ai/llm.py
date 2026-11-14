"""
ai.llm — Groq LLM Client
===========================
Sends user queries to Groq's chat completion API and returns
the assistant's response.

Model: openai/gpt-oss-120b (cloud-based, via Groq infrastructure).

Dependencies:
  - groq (official Groq Python SDK)
"""

import logging
from typing import Optional

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
                 system_prompt: Optional[str] = None):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for the LLM.")
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout
        self._system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self._client = None  # lazy init
        logger.info(f"LLMClient: model={model}, max_tokens={max_tokens}")

    # ── Lazy client ───────────────────────────────────────────

    def _ensure_client(self):
        """Create the Groq client on first use (not on import)."""
        if self._client is None:
            from groq import Groq
            self._client = Groq(
                api_key=self._api_key,
                timeout=self._timeout,
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

        self._ensure_client()

        # Build the messages list
        messages = [{"role": "system", "content": self._system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )
            response = completion.choices[0].message.content.strip()
            logger.info(
                f"LLM response: '{response[:80]}{'…' if len(response) > 80 else ''}'"
            )
            return response

        except Exception as e:
            logger.error(f"LLM API error: {type(e).__name__}: {e}")
            return ""
