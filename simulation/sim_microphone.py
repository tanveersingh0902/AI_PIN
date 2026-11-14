"""
simulation.sim_microphone — Simulated Microphone
==================================================
Drop-in replacement for PiMicrophone on Windows / dev machines.

Behaviour:
  - If PyAudio is installed, records from the system default mic
    (laptop microphone) — useful for real end-to-end testing.
  - If PyAudio is NOT installed, generates silent audio frames
    so the pipeline can still run without errors.

Implements hardware.microphone.MicrophoneInterface.
"""

import logging
import threading
import time

from hardware.microphone import MicrophoneInterface

logger = logging.getLogger(__name__)


# ── Check PyAudio availability ─────────────────────────────────
_HAS_PYAUDIO = False
try:
    import pyaudio as _pa
    _HAS_PYAUDIO = True
except ImportError:
    pass


class SimMicrophone(MicrophoneInterface):
    """
    Simulated microphone for Windows development.

    Uses the system default microphone via PyAudio when available,
    otherwise generates silent PCM frames so the rest of the
    pipeline can run unchanged.
    """

    SAMPLE_WIDTH = 2  # 16-bit

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 1024):
        self._sample_rate = sample_rate
        self._channels = channels
        self._chunk_size = chunk_size
        self._frames: list[bytes] = []
        self._recording = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # PyAudio (optional)
        self._audio = None
        if _HAS_PYAUDIO:
            try:
                self._audio = _pa.PyAudio()
                logger.info("SimMicrophone: using system microphone via PyAudio.")
            except Exception as e:
                logger.warning(f"SimMicrophone: PyAudio init failed ({e}), using silence.")
                self._audio = None
        else:
            logger.info("SimMicrophone: PyAudio not installed — generating silence.")

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

    # ── Recording (background thread) ─────────────────────────

    def start_recording(self) -> None:
        if self._recording:
            logger.warning("SimMicrophone: already recording.")
            return
        self._frames = []
        self._recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        logger.info("SimMicrophone: recording started.")

    def _record_loop(self):
        if self._audio:
            self._record_loop_pyaudio()
        else:
            self._record_loop_silence()

    def _record_loop_pyaudio(self):
        """Record from the real system mic via PyAudio."""
        try:
            stream = self._audio.open(
                format=_pa.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._chunk_size,
            )
            while self._recording:
                data = stream.read(self._chunk_size, exception_on_overflow=False)
                with self._lock:
                    self._frames.append(data)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error(f"SimMicrophone PyAudio error: {e}")
            self._recording = False

    def _record_loop_silence(self):
        """Generate silent frames at the correct rate."""
        bytes_per_chunk = self._chunk_size * self.SAMPLE_WIDTH * self._channels
        interval = self._chunk_size / self._sample_rate
        while self._recording:
            with self._lock:
                self._frames.append(b"\x00" * bytes_per_chunk)
            time.sleep(interval)

    def stop_recording(self) -> bytes:
        if not self._recording:
            return b""
        self._recording = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        with self._lock:
            audio = b"".join(self._frames)
            self._frames = []
        logger.info(f"SimMicrophone: captured {len(audio)} bytes.")
        return audio

    # ── Fixed-duration recording (blocking) ────────────────────

    def record(self, duration: float) -> bytes:
        if self._audio:
            return self._record_pyaudio(duration)
        return self._record_silence(duration)

    def _record_pyaudio(self, duration: float) -> bytes:
        try:
            stream = self._audio.open(
                format=_pa.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._chunk_size,
            )
            frames = []
            num_chunks = int(self._sample_rate / self._chunk_size * duration)
            logger.info(f"SimMicrophone: recording {duration}s from system mic …")
            for _ in range(num_chunks):
                data = stream.read(self._chunk_size, exception_on_overflow=False)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            audio = b"".join(frames)
            logger.info(f"SimMicrophone: captured {len(audio)} bytes.")
            return audio
        except Exception as e:
            logger.error(f"SimMicrophone record error: {e}")
            return b""

    def _record_silence(self, duration: float) -> bytes:
        num_samples = int(self._sample_rate * duration)
        audio = b"\x00" * (num_samples * self.SAMPLE_WIDTH * self._channels)
        logger.info(f"SimMicrophone: generated {len(audio)} bytes of silence ({duration}s).")
        return audio

    # ── Cleanup ────────────────────────────────────────────────

    def cleanup(self) -> None:
        self._recording = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None
        logger.info("SimMicrophone: cleaned up.")
