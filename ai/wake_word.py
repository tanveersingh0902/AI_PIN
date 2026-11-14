"""
ai.wake_word — Wake-Word Detection
====================================
Listens for the trigger phrase (e.g., "Hey Vihaan") to activate the
voice assistant pipeline.

Approaches (in order of preference for Pi Zero W):
  1. Simple keyword spotting using SpeechRecognition (low CPU)
  2. Porcupine / openWakeWord (if RAM permits)
  3. Custom lightweight model (future)

The wake word is configured via config.settings.WAKE_WORD.
"""

import logging

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Lightweight wake-word detector.

    TODO: Implement detect() — start with keyword matching on
          continuous STT output, then optimise.
    """

    def __init__(self, wake_word: str = "hey vihaan"):
        self.wake_word = wake_word.lower().strip()
        logger.info(f"Wake word set to: '{self.wake_word}'")

    def detect(self, audio_data: bytes) -> bool:
        """
        Check if the wake word is present in the audio.

        Parameters
        ----------
        audio_data : bytes
            A short audio chunk to analyse.

        Returns
        -------
        bool
            True if the wake word was detected.
        """
        logger.warning("WakeWordDetector.detect() not yet implemented.")
        return False
