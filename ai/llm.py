"""
ai.llm — Large Language Model Interface
==========================================
Sends user queries to a cloud LLM and returns responses.

Supported providers:
  - "gemini" : Google Gemini API (default — fast, free tier available)
  - "openai" : OpenAI ChatGPT API
  - "local"  : Reserved for future on-device small model

Responses are kept short (max_tokens) to save bandwidth and Pi RAM.
"""

import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Lightweight LLM client.

    TODO: Implement query() with google-genai or openai SDK.
    """

    # System prompt tailored for a wearable voice assistant
    DEFAULT_SYSTEM_PROMPT = (
        "You are VIHAAN, a helpful, concise voice assistant running on a "
        "wearable AI pin. Keep responses short (1–3 sentences) and spoken-"
        "language friendly. Avoid markdown, code blocks, or long lists."
    )

    def __init__(self, provider: str = "gemini", model: str = "gemini-2.0-flash",
                 api_key: str = "", max_tokens: int = 256,
                 temperature: float = 0.7):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        logger.info(f"LLM provider: {provider} | model: {model}")

    def query(self, user_message: str, conversation_history: list | None = None) -> str:
        """
        Send a message to the LLM and return the text response.

        Parameters
        ----------
        user_message : str
            What the user said.
        conversation_history : list, optional
            Prior turns for context (kept minimal to save RAM).

        Returns
        -------
        str
            The assistant's reply.
        """
        logger.warning("LLMClient.query() not yet implemented.")
        return ""
