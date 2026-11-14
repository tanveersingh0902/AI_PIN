"""
hardware.mic — Microphone Input Driver
=======================================
Captures audio from the microphone connected to the Raspberry Pi.
Supports I2S MEMS microphones (e.g., INMP441) or USB microphones.

On the Pi this uses PyAudio with ALSA backend.
On Windows the simulation layer substitutes this module.
"""

from abc import ABC, abstractmethod


class BaseMicrophone(ABC):
    """Interface that both real and simulated microphones implement."""

    @abstractmethod
    def start_stream(self) -> None:
        """Open the audio input stream."""
        ...

    @abstractmethod
    def read_chunk(self) -> bytes:
        """Read one chunk of raw audio data."""
        ...

    @abstractmethod
    def stop_stream(self) -> None:
        """Close the audio input stream and release resources."""
        ...


class Microphone(BaseMicrophone):
    """
    Real microphone driver for Raspberry Pi.

    TODO: Implement with PyAudio when deploying on the Pi.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self._stream = None

    def start_stream(self) -> None:
        raise NotImplementedError("Real mic driver not yet implemented.")

    def read_chunk(self) -> bytes:
        raise NotImplementedError

    def stop_stream(self) -> None:
        raise NotImplementedError
