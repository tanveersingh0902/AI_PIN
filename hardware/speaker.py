"""
hardware.speaker — Speaker Interface & Pi Implementation
==========================================================
Defines the SpeakerInterface ABC and the PiSpeaker driver for the
MAX98357A I2S amplifier + speaker on Raspberry Pi Zero W.

Plays WAV files and raw PCM audio.  Supports stop_playback() to
interrupt playback mid-stream.

Pi-specific dependencies (lazy-imported):
  - pyaudio
"""

import wave
import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Interface ──────────────────────────────────────────────────

class SpeakerInterface(ABC):
    """
    Abstract speaker interface.

    All speaker implementations (real and simulated) must implement
    this interface.
    """

    @abstractmethod
    def play_wav(self, filepath: str) -> None:
        """
        Play a WAV audio file.

        Parameters
        ----------
        filepath : str
            Path to the WAV file.
        """
        ...

    @abstractmethod
    def play_audio(self, audio_data: bytes, sample_rate: int = 16000,
                   channels: int = 1) -> None:
        """
        Play raw 16-bit PCM audio data.

        Parameters
        ----------
        audio_data : bytes
            Raw PCM audio.
        sample_rate : int
            Sample rate in Hz.
        channels : int
            Number of audio channels.
        """
        ...

    @property
    @abstractmethod
    def is_playing(self) -> bool:
        """Return True if audio is currently playing."""
        ...

    @abstractmethod
    def stop_playback(self) -> None:
        """Stop any currently playing audio immediately."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release audio resources."""
        ...


# ── Raspberry Pi Implementation ───────────────────────────────

class PiSpeaker(SpeakerInterface):
    """
    Real speaker driver for MAX98357A I2S amplifier on Raspberry Pi.

    Uses PyAudio to stream audio to the I2S output device.
    Playback runs in a background thread so it doesn't block the
    main assistant loop.

    Parameters
    ----------
    chunk_size : int
        Frames per output buffer (default 1024).
    device_index : int or None
        ALSA output device index.  If None, uses the default.
    """

    def __init__(self, chunk_size: int = 1024,
                 device_index: int | None = None):
        self._chunk_size = chunk_size
        self._device_index = device_index
        self._audio = None
        self._playing = False
        self._play_thread: threading.Thread | None = None

    @property
    def is_playing(self) -> bool:
        return self._playing

    def _ensure_audio(self):
        if self._audio is None:
            import pyaudio
            self._audio = pyaudio.PyAudio()

    def play_wav(self, filepath: str) -> None:
        path = Path(filepath)
        if not path.is_file():
            logger.error(f"WAV file not found: {filepath}")
            return

        self.stop_playback()
        self._playing = True
        self._play_thread = threading.Thread(
            target=self._play_wav_worker, args=(str(path),), daemon=True
        )
        self._play_thread.start()

    def _play_wav_worker(self, filepath: str):
        try:
            import pyaudio
            self._ensure_audio()

            with wave.open(filepath, "rb") as wf:
                stream = self._audio.open(
                    format=self._audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=self._device_index,
                    frames_per_buffer=self._chunk_size,
                )
                logger.info(f"PiSpeaker: playing '{filepath}'")
                data = wf.readframes(self._chunk_size)
                while data and self._playing:
                    stream.write(data)
                    data = wf.readframes(self._chunk_size)

                stream.stop_stream()
                stream.close()
        except Exception as e:
            logger.error(f"PiSpeaker playback error: {e}")
        finally:
            self._playing = False

    def play_audio(self, audio_data: bytes, sample_rate: int = 16000,
                   channels: int = 1) -> None:
        self.stop_playback()
        self._playing = True
        self._play_thread = threading.Thread(
            target=self._play_raw_worker,
            args=(audio_data, sample_rate, channels),
            daemon=True,
        )
        self._play_thread.start()

    def _play_raw_worker(self, audio_data: bytes, sample_rate: int,
                         channels: int):
        try:
            import pyaudio
            self._ensure_audio()

            stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                output=True,
                output_device_index=self._device_index,
                frames_per_buffer=self._chunk_size,
            )
            offset = 0
            chunk_bytes = self._chunk_size * 2 * channels  # 16-bit
            logger.info(f"PiSpeaker: playing {len(audio_data)} bytes of raw audio.")
            while offset < len(audio_data) and self._playing:
                chunk = audio_data[offset:offset + chunk_bytes]
                stream.write(chunk)
                offset += chunk_bytes

            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error(f"PiSpeaker raw playback error: {e}")
        finally:
            self._playing = False

    def stop_playback(self) -> None:
        self._playing = False
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2.0)
            self._play_thread = None
        logger.debug("PiSpeaker: playback stopped.")

    def cleanup(self) -> None:
        self.stop_playback()
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None
        logger.info("PiSpeaker: cleaned up.")
