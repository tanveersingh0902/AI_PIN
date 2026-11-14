"""
simulation.sim_speaker — Simulated Speaker
============================================
Replaces the real speaker on Windows for development.
Plays audio through the Windows default output device, or logs
to console in headless / CI environments.

Implements hardware.speaker.BaseSpeaker interface.
"""

import logging
from hardware.speaker import BaseSpeaker

logger = logging.getLogger(__name__)


class SimSpeaker(BaseSpeaker):
    """
    Simulated speaker for Windows development.

    TODO: Implement with PyAudio or sounddevice for real playback.
    """

    def play_audio(self, audio_data: bytes) -> None:
        logger.info(f"SimSpeaker: playing {len(audio_data)} bytes of audio (simulated).")

    def play_file(self, filepath: str) -> None:
        logger.info(f"SimSpeaker: playing file '{filepath}' (simulated).")

    def stop(self) -> None:
        logger.info("SimSpeaker: playback stopped.")
