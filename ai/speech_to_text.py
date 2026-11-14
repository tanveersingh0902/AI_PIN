"""
ai.speech_to_text — Groq Whisper Speech-to-Text
=================================================
Sends recorded audio to Groq's Whisper API and returns the
transcribed text.

Model: whisper-large-v3-turbo (cloud-based, fast, accurate).

This module does NOT record audio.  It receives audio data or a
file path from the hardware layer and handles only the
cloud-transcription step.

Dependencies:
  - groq (official Groq Python SDK)
"""

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Groq Whisper speech-to-text client.

    Parameters
    ----------
    api_key : str
        Groq API key (from env, never hardcoded).
    model : str
        Whisper model name on Groq.
    timeout : float
        HTTP request timeout in seconds.
    """

    def __init__(self, api_key: str, model: str = "whisper-large-v3-turbo",
                 timeout: float = 30.0):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for speech-to-text.")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._client = None  # lazy init
        logger.info(f"SpeechToText: model={model}")

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

    def transcribe_file(self, filepath: str) -> str:
        """
        Transcribe an audio file via Groq Whisper.

        Parameters
        ----------
        filepath : str
            Path to a WAV, MP3, or other supported audio file.

        Returns
        -------
        str
            The transcribed text, or empty string on failure.
        """
        path = Path(filepath)
        if not path.is_file():
            logger.error(f"STT: audio file not found: {filepath}")
            return ""

        if path.stat().st_size == 0:
            logger.warning("STT: audio file is empty, skipping.")
            return ""

        self._ensure_client()

        try:
            with open(path, "rb") as audio_file:
                transcription = self._client.audio.transcriptions.create(
                    file=(path.name, audio_file),
                    model=self._model,
                    response_format="text",
                    language="en",
                )
            text = str(transcription).strip()
            logger.info(f"STT result: '{text[:80]}{'…' if len(text) > 80 else ''}'")
            return text

        except Exception as e:
            logger.error(f"STT API error: {type(e).__name__}: {e}")
            return ""

    def transcribe_bytes(self, audio_data: bytes,
                         filename: str = "recording.wav") -> str:
        """
        Transcribe raw audio bytes via Groq Whisper.

        Parameters
        ----------
        audio_data : bytes
            Audio content (WAV format with headers).
        filename : str
            Virtual filename hint for the API.

        Returns
        -------
        str
            The transcribed text, or empty string on failure.
        """
        if not audio_data:
            logger.warning("STT: empty audio data, skipping.")
            return ""

        self._ensure_client()

        try:
            audio_file = io.BytesIO(audio_data)
            transcription = self._client.audio.transcriptions.create(
                file=(filename, audio_file),
                model=self._model,
                response_format="text",
                language="en",
            )
            text = str(transcription).strip()
            logger.info(f"STT result: '{text[:80]}{'…' if len(text) > 80 else ''}'")
            return text

        except Exception as e:
            logger.error(f"STT API error: {type(e).__name__}: {e}")
            return ""
