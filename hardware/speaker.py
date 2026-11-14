"""
hardware.speaker — Audio Output Driver
========================================
Plays synthesised speech and feedback sounds through the speaker
connected to the Raspberry Pi (I2S DAC, PWM, or USB audio).

On the Pi this uses PyAudio or aplay.
On Windows the simulation layer substitutes this module.
"""

from abc import ABC, abstractmethod


class BaseSpeaker(ABC):
    """Interface for audio output."""

    @abstractmethod
    def play_audio(self, audio_data: bytes) -> None:
        """Play raw PCM audio data."""
        ...

    @abstractmethod
    def play_file(self, filepath: str) -> None:
        """Play an audio file (WAV/MP3)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop playback and release resources."""
        ...


class Speaker(BaseSpeaker):
    """
    Real speaker driver for Raspberry Pi.

    TODO: Implement with PyAudio / aplay when deploying on the Pi.
    """

    def play_audio(self, audio_data: bytes) -> None:
        raise NotImplementedError("Real speaker driver not yet implemented.")

    def play_file(self, filepath: str) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError
