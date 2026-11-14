"""
ai.stt — Speech-to-Text Engine
================================
Converts microphone audio into text.

Supported backends:
  - "google"  : Google Web Speech API (free, needs internet)
  - "vosk"    : Vosk offline recogniser (low RAM, runs on Pi)
  - "whisper" : OpenAI Whisper API (cloud, high accuracy)

The backend is selected via config.settings.STT_ENGINE.
"""

import logging

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Lightweight STT wrapper.

    TODO: Implement recognise() with SpeechRecognition library.
    """

    def __init__(self, engine: str = "google"):
        self.engine = engine
        logger.info(f"STT engine selected: {engine}")

    def recognise(self, audio_data: bytes) -> str:
        """
        Convert raw audio bytes to text.

        Parameters
        ----------
        audio_data : bytes
            Raw PCM audio captured from the microphone.

        Returns
        -------
        str
            Recognised text, or empty string on failure.
        """
        # Placeholder — will be implemented in the next phase
        logger.warning("STT.recognise() not yet implemented.")
        return ""
