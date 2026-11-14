"""
simulation.sim_mic — Simulated Microphone
===========================================
Replaces the real microphone on Windows for development.

Two modes:
  1. FILE mode  — reads audio from a WAV file (for automated testing)
  2. SYSTEM mode — uses the Windows default microphone via PyAudio

Implements hardware.mic.BaseMicrophone interface.
"""

import logging
from hardware.mic import BaseMicrophone

logger = logging.getLogger(__name__)


class SimMicrophone(BaseMicrophone):
    """
    Simulated microphone for Windows development.

    TODO: Implement with PyAudio system mic or WAV file reading.
    """

    def __init__(self, source: str = "system", wav_path: str = ""):
        self.source = source   # "system" or "file"
        self.wav_path = wav_path
        logger.info(f"SimMicrophone initialised (source={source})")

    def start_stream(self) -> None:
        logger.info("SimMicrophone: stream started (simulated).")

    def read_chunk(self) -> bytes:
        logger.debug("SimMicrophone: returning empty audio chunk.")
        return b"\x00" * 1024  # Silence placeholder

    def stop_stream(self) -> None:
        logger.info("SimMicrophone: stream stopped.")
