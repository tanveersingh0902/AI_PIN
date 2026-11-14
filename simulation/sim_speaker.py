"""
simulation.sim_speaker — Simulated Speaker
=============================================
Drop-in replacement for PiSpeaker on Windows / dev machines.

Behaviour:
  - If PyAudio is installed, plays audio through the system
    default output device (laptop speakers / headphones).
  - Falls back to winsound (Windows stdlib) for WAV playback.
  - If neither is available, logs playback events to console.

Implements hardware.speaker.SpeakerInterface.
"""

import wave
import logging
import threading
import sys
from pathlib import Path

from hardware.speaker import SpeakerInterface

logger = logging.getLogger(__name__)

# ── Check available backends ───────────────────────────────────
_HAS_PYAUDIO = False
_HAS_WINSOUND = False
try:
    import pyaudio as _pa
    _HAS_PYAUDIO = True
except ImportError:
    pass
if sys.platform == "win32":
    try:
        import winsound as _ws
        _HAS_WINSOUND = True
    except ImportError:
        pass


class SimSpeaker(SpeakerInterface):
    """
    Simulated speaker for Windows development.

    Attempts real audio playback through PyAudio or winsound.
    Falls back to console logging if no audio backend is available.
    """

    def __init__(self):
        self._playing = False
        self._play_thread: threading.Thread | None = None
        self._audio = None

        if _HAS_PYAUDIO:
            try:
                self._audio = _pa.PyAudio()
                logger.info("SimSpeaker: using PyAudio for playback.")
            except Exception:
                self._audio = None
        if self._audio is None and _HAS_WINSOUND:
            logger.info("SimSpeaker: using winsound for WAV playback.")
        elif self._audio is None:
            logger.info("SimSpeaker: no audio backend — logging only.")

    @property
    def is_playing(self) -> bool:
        return self._playing

    # ── WAV playback ──────────────────────────────────────────

    def play_wav(self, filepath: str) -> None:
        path = Path(filepath)
        if not path.is_file():
            logger.error(f"SimSpeaker: WAV file not found: {filepath}")
            return

        self.stop_playback()
        self._playing = True
        self._play_thread = threading.Thread(
            target=self._play_wav_worker, args=(str(path),), daemon=True
        )
        self._play_thread.start()

    def _play_wav_worker(self, filepath: str):
        try:
            if self._audio:
                self._play_wav_pyaudio(filepath)
            elif _HAS_WINSOUND:
                logger.info(f"SimSpeaker ▶ playing '{filepath}' (winsound)")
                _ws.PlaySound(filepath, _ws.SND_FILENAME)
            else:
                logger.info(f"SimSpeaker ▶ [LOG ONLY] playing '{filepath}'")
        except Exception as e:
            logger.error(f"SimSpeaker playback error: {e}")
        finally:
            self._playing = False

    def _play_wav_pyaudio(self, filepath: str):
        with wave.open(filepath, "rb") as wf:
            stream = self._audio.open(
                format=self._audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )
            logger.info(f"SimSpeaker ▶ playing '{filepath}' (PyAudio)")
            data = wf.readframes(1024)
            while data and self._playing:
                stream.write(data)
                data = wf.readframes(1024)
            stream.stop_stream()
            stream.close()

    # ── Raw audio playback ────────────────────────────────────

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
            if self._audio:
                stream = self._audio.open(
                    format=_pa.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    output=True,
                )
                offset = 0
                chunk_bytes = 1024 * 2 * channels
                logger.info(f"SimSpeaker ▶ playing {len(audio_data)} bytes (PyAudio)")
                while offset < len(audio_data) and self._playing:
                    stream.write(audio_data[offset:offset + chunk_bytes])
                    offset += chunk_bytes
                stream.stop_stream()
                stream.close()
            else:
                logger.info(
                    f"SimSpeaker ▶ [LOG ONLY] {len(audio_data)} bytes raw audio"
                )
        except Exception as e:
            logger.error(f"SimSpeaker raw playback error: {e}")
        finally:
            self._playing = False

    # ── Controls ──────────────────────────────────────────────

    def stop_playback(self) -> None:
        self._playing = False
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2.0)
            self._play_thread = None
        logger.debug("SimSpeaker: playback stopped.")

    def cleanup(self) -> None:
        self.stop_playback()
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None
        logger.info("SimSpeaker: cleaned up.")
