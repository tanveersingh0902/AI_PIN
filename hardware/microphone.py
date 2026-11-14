"""
hardware.microphone — Microphone Interface & Pi Implementation
================================================================
Defines the MicrophoneInterface ABC and the PiMicrophone driver
for the INMP441 I2S MEMS microphone on Raspberry Pi Zero W.

Audio format: 16-bit PCM, mono, 16 kHz (configurable).
WAV output uses Python's stdlib `wave` module — zero extra deps.

Pi-specific dependencies (lazy-imported):
  - pyaudio
"""

from __future__ import annotations

import io
import wave
import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Interface ──────────────────────────────────────────────────

class MicrophoneInterface(ABC):
    """
    Abstract microphone interface.

    All microphone implementations (real and simulated) must
    implement this interface so the rest of the codebase stays
    platform-independent.
    """

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Return the configured sample rate in Hz."""
        ...

    @property
    @abstractmethod
    def channels(self) -> int:
        """Return the number of audio channels (1 = mono)."""
        ...

    @property
    @abstractmethod
    def is_recording(self) -> bool:
        """Return True if recording is in progress."""
        ...

    @abstractmethod
    def start_recording(self) -> None:
        """
        Begin capturing audio in the background (non-blocking).
        Audio frames are buffered internally until stop_recording().
        """
        ...

    @abstractmethod
    def stop_recording(self) -> bytes:
        """
        Stop capturing and return the recorded raw PCM audio bytes.

        Returns
        -------
        bytes
            Raw 16-bit PCM audio data.
        """
        ...

    @abstractmethod
    def record(self, duration: float) -> bytes:
        """
        Record audio for a fixed duration (blocking).

        Parameters
        ----------
        duration : float
            Recording length in seconds.

        Returns
        -------
        bytes
            Raw 16-bit PCM audio data.
        """
        ...

    def save_wav(self, audio_data: bytes, filepath: str) -> str:
        """
        Save raw PCM audio data as a WAV file.

        This is a concrete method shared by all implementations
        because the WAV format is platform-independent.

        Parameters
        ----------
        audio_data : bytes
            Raw 16-bit PCM audio.
        filepath : str
            Destination file path.

        Returns
        -------
        str
            The absolute path of the saved WAV file.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)

        logger.info(f"WAV saved: {path} ({len(audio_data)} bytes)")
        return str(path.resolve())

    @abstractmethod
    def cleanup(self) -> None:
        """Release audio resources."""
        ...


# ── Raspberry Pi Implementation ───────────────────────────────

class PiMicrophone(MicrophoneInterface):
    """
    Real microphone driver for INMP441 I2S mic on Raspberry Pi.

    Uses PyAudio with the ALSA backend.  The I2S device must be
    configured in /boot/config.txt and the ALSA overlay loaded
    before this class can open the audio stream.

    Parameters
    ----------
    sample_rate : int
        Sampling rate in Hz (default 16000).
    channels : int
        Number of channels (default 1 = mono).
    chunk_size : int
        Frames per buffer (default 1024).
    device_index : int or None
        ALSA device index for the I2S mic.  If None, the default
        input device is used.
    """

    SAMPLE_WIDTH = 2  # 16-bit

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 1024, device_index: int | None = None):
        self._sample_rate = sample_rate
        self._channels = channels
        self._chunk_size = chunk_size
        self._device_index = device_index

        self._audio = None          # PyAudio instance (lazy)
        self._stream = None
        self._frames: list[bytes] = []
        self._recording = False
        self._record_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ── Properties ────────────────────────────────────────────

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def is_recording(self) -> bool:
        return self._recording

    # ── Private helpers ───────────────────────────────────────

    def _ensure_audio(self):
        """Lazy-init PyAudio (avoids import on Windows)."""
        if self._audio is None:
            import pyaudio
            self._audio = pyaudio.PyAudio()
            logger.debug("PyAudio initialised.")

    def _open_stream(self):
        """Open an input stream on the configured device."""
        import pyaudio
        kwargs = dict(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._sample_rate,
            input=True,
            frames_per_buffer=self._chunk_size,
        )
        if self._device_index is not None:
            kwargs["input_device_index"] = self._device_index
        return self._audio.open(**kwargs)

    def _record_loop(self):
        """Background recording loop (runs in a thread)."""
        stream = None
        try:
            stream = self._open_stream()
            self._stream = stream
            logger.info("PiMicrophone: recording started.")
            while self._recording:
                try:
                    data = stream.read(self._chunk_size,
                                       exception_on_overflow=False)
                    with self._lock:
                        self._frames.append(data)
                except Exception as e:
                    logger.error(f"Mic read error: {e}")
                    break
        except Exception as e:
            logger.error(f"PiMicrophone recording failed: {e}")
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                except Exception:
                    logger.debug("PiMicrophone stream stop failed.", exc_info=True)
                try:
                    stream.close()
                except Exception:
                    logger.warning(
                        "PiMicrophone stream close failed.", exc_info=True
                    )
            self._stream = None
            self._recording = False

    # ── Public API ────────────────────────────────────────────

    def start_recording(self) -> None:
        if self._recording:
            logger.warning("Already recording.")
            return
        if self._record_thread and self._record_thread.is_alive():
            raise RuntimeError("Previous microphone recording is still active.")
        self._record_thread = None
        self._ensure_audio()
        self._frames = []
        self._recording = True
        self._record_thread = threading.Thread(
            target=self._record_loop, daemon=True
        )
        self._record_thread.start()

    def stop_recording(self) -> bytes:
        if not self._recording and self._record_thread is None:
            logger.warning("Not currently recording.")
            return b""
        self._recording = False
        thread = self._record_thread
        if thread:
            thread.join(timeout=3.0)
            if thread.is_alive():
                raise RuntimeError("Microphone recording did not stop in time.")
            self._record_thread = None
        with self._lock:
            audio_data = b"".join(self._frames)
            self._frames = []
        logger.info(f"PiMicrophone: captured {len(audio_data)} bytes.")
        return audio_data

    def record(self, duration: float) -> bytes:
        self._ensure_audio()
        stream = self._open_stream()
        frames: list[bytes] = []
        num_chunks = int(self._sample_rate / self._chunk_size * duration)

        logger.info(f"PiMicrophone: recording {duration}s …")
        try:
            for _ in range(num_chunks):
                data = stream.read(self._chunk_size,
                                   exception_on_overflow=False)
                frames.append(data)
        except Exception as e:
            logger.error(f"PiMicrophone record error: {e}")
        finally:
            try:
                stream.stop_stream()
            except Exception:
                logger.debug("PiMicrophone stream stop failed.", exc_info=True)
            try:
                stream.close()
            except Exception:
                logger.warning("PiMicrophone stream close failed.", exc_info=True)

        audio_data = b"".join(frames)
        logger.info(f"PiMicrophone: captured {len(audio_data)} bytes.")
        return audio_data

    def cleanup(self) -> None:
        self._recording = False
        thread = self._record_thread
        if thread:
            thread.join(timeout=3.0)
        if thread and thread.is_alive() and self._stream:
            try:
                self._stream.stop_stream()
            except Exception:
                logger.debug("Could not interrupt microphone stream.", exc_info=True)
            thread.join(timeout=1.0)
        if thread and thread.is_alive():
            logger.error("Microphone recording thread did not stop; audio retained.")
            return
        self._record_thread = None
        with self._lock:
            self._frames = []
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                logger.warning("PyAudio termination failed.", exc_info=True)
            self._audio = None
        logger.info("PiMicrophone: cleaned up.")
