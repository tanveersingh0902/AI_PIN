"""
ai.tts — Text-to-Speech Engine
================================
Converts text responses into spoken audio.

Supported backends:
  - "pyttsx3" : Offline TTS (uses SAPI5 on Windows, espeak on Linux)
  - "espeak"  : Direct espeak call (Pi only, very lightweight)
  - "cloud"   : Google / cloud TTS API (high quality, needs internet)

The backend is selected via config.settings.TTS_ENGINE.
"""

import logging

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Lightweight TTS wrapper.

    TODO: Implement speak() with pyttsx3 / espeak.
    """

    def __init__(self, engine: str = "pyttsx3"):
        self.engine = engine
        logger.info(f"TTS engine selected: {engine}")

    def speak(self, text: str) -> None:
        """
        Synthesise and play speech from text.

        Parameters
        ----------
        text : str
            The text to speak aloud.
        """
        logger.warning("TTS.speak() not yet implemented.")

    def speak_to_bytes(self, text: str) -> bytes:
        """
        Synthesise speech and return raw audio bytes (for streaming).

        Returns
        -------
        bytes
            Raw PCM audio.
        """
        logger.warning("TTS.speak_to_bytes() not yet implemented.")
        return b""
