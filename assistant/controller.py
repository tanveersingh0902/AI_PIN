"""Coordinates button input, audio capture, AI processing, and playback."""

from __future__ import annotations

import logging
import queue
import tempfile
import threading
import time
import wave
from enum import Enum, auto
from pathlib import Path

from ai.pipeline import AIPipeline
from ai.text_to_speech import TextToSpeech
from backend.network_manager import NetworkManager
from hardware.display import DisplayStatus
from hardware.factory import HardwareKit
from utils.platform_detect import Platform

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    INITIALIZING = auto()
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    ERROR = auto()
    SHUTDOWN = auto()


class AssistantController:
    """Runs the push-to-talk conversation loop using injected components."""

    def __init__(
        self,
        hardware: HardwareKit,
        ai_pipeline: AIPipeline,
        tts: TextToSpeech,
        recording_dir: str | Path | None = None,
        network_manager: NetworkManager | None = None,
    ):
        self.hardware = hardware
        self.ai_pipeline = ai_pipeline
        self.tts = tts
        self.network_manager = network_manager
        self.recording_dir = Path(recording_dir or tempfile.gettempdir())
        self._events: queue.Queue[str] = queue.Queue()
        self._state = AssistantState.INITIALIZING
        self._state_lock = threading.Lock()
        self._shutdown_lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._running = False
        self._shutdown_complete = False
        self._deferred_cleanup = False
        self._press_active = False
        self._temporary_files: set[Path] = set()

    @property
    def state(self) -> AssistantState:
        with self._state_lock:
            return self._state

    def run(self) -> bool:
        """Register short button callbacks and process events on this thread."""
        self._running = True
        succeeded = True
        try:
            self.hardware.button.on_press(self._on_button_press)
            self.hardware.button.on_release(self._on_button_release)
            self._set_state(AssistantState.IDLE, "VIHAAN READY", DisplayStatus.IDLE)
            logger.info("VIHAAN is ready. Hold the button to record.")

            if self.hardware.platform != Platform.RASPBERRY_PI:
                self.hardware.button.wait_for_press(timeout=0)

            while self._running:
                try:
                    event = self._events.get(timeout=0.25)
                except queue.Empty:
                    continue
                if event == "press":
                    self._handle_button_press()
                elif event == "release":
                    self._handle_button_release()
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
        except Exception:
            logger.exception("Assistant stopped after an unexpected error.")
            succeeded = False
            if self.state != AssistantState.SHUTDOWN:
                self._set_state(AssistantState.ERROR, "ERROR", DisplayStatus.ERROR)
        finally:
            self.shutdown()
        return succeeded

    def stop(self) -> None:
        """Request the run loop to stop."""
        self._running = False
        self._events.put("shutdown")
        self.shutdown()

    def shutdown(self) -> None:
        """Stop active audio and release hardware resources, once."""
        with self._shutdown_lock:
            if self._shutdown_complete:
                return
            self._shutdown_complete = True
            self._running = False
            self._shutdown_event.set()
            active_work = self.state in (
                AssistantState.PROCESSING,
                AssistantState.SPEAKING,
            )
            self._deferred_cleanup = active_work
        if active_work:
            try:
                self.hardware.speaker.stop_playback()
            except Exception:
                logger.exception("Could not stop speaker during shutdown.")
            self._set_state(AssistantState.SHUTDOWN)
            logger.info("Hardware cleanup deferred until active work ends.")
            return

        if self.hardware.microphone.is_recording:
            try:
                self.hardware.microphone.stop_recording()
            except Exception:
                logger.exception("Could not stop microphone during shutdown.")
        try:
            self.hardware.speaker.stop_playback()
        except Exception:
            logger.exception("Could not stop speaker during shutdown.")
        self._cleanup_temporary_files()
        self.hardware.cleanup()
        self._set_state(AssistantState.SHUTDOWN)
        logger.info("VIHAAN shut down cleanly.")

    def _on_button_press(self) -> None:
        self._events.put("press")

    def _on_button_release(self) -> None:
        self._events.put("release")

    def _handle_button_press(self) -> None:
        if self.state != AssistantState.IDLE or self._press_active:
            return
        self._press_active = True
        self._set_state(
            AssistantState.LISTENING, "LISTENING", DisplayStatus.LISTENING
        )
        try:
            self.hardware.microphone.start_recording()
        except Exception as exc:
            self._press_active = False
            self._recover_from_error(f"Microphone could not start: {exc}")

    def _handle_button_release(self) -> None:
        if self.state != AssistantState.LISTENING or not self._press_active:
            return
        self._press_active = False
        self._set_state(
            AssistantState.PROCESSING, "PROCESSING", DisplayStatus.THINKING
        )
        try:
            self._process_recording()
        except Exception as exc:
            self._recover_from_error(f"Voice interaction failed: {exc}")
        finally:
            with self._shutdown_lock:
                if (
                    not self._shutdown_complete
                    and self.state not in (AssistantState.SHUTDOWN, AssistantState.IDLE)
                ):
                    self._set_state(
                        AssistantState.IDLE, "VIHAAN READY", DisplayStatus.IDLE
                    )
            self._discard_queued_button_events()
            self._finish_deferred_cleanup()

    def _finish_deferred_cleanup(self) -> None:
        with self._shutdown_lock:
            if not self._deferred_cleanup:
                return
            self._deferred_cleanup = False
        self._cleanup_temporary_files()
        self.hardware.cleanup()
        logger.info("VIHAAN hardware cleanup completed after active work.")

    def _process_recording(self) -> None:
        audio_data = self.hardware.microphone.stop_recording()
        if self._shutdown_event.is_set():
            return
        if not audio_data:
            logger.warning("No audio was captured; waiting for the next press.")
            return
        channels = self.hardware.microphone.channels
        frame_size = 2 * channels
        if (
            channels <= 0
            or len(audio_data) < frame_size
            or len(audio_data) % frame_size
        ):
            logger.warning("Microphone returned an incomplete PCM frame.")
            return

        recording_path = self._new_temporary_file()
        try:
            self.hardware.microphone.save_wav(audio_data, str(recording_path))
            del audio_data
            if not self._has_usable_audio(recording_path):
                logger.info("Recording is empty or silent; skipping AI requests.")
                return

            if (
                self.network_manager is not None
                and not self.network_manager.check_status().internet_available
            ):
                self._announce_offline()
                return

            if self._shutdown_event.is_set():
                return
            result = self.ai_pipeline.process_audio_file(
                str(recording_path), speak=False
            )
            if self._shutdown_event.is_set():
                return
            if result.error:
                if (
                    self.network_manager is not None
                    and not self.network_manager.check_status().internet_available
                ):
                    self._announce_offline()
                    return
                detail = self._last_ai_error()
                message = f"AI pipeline failed: {result.error}"
                if detail:
                    message = f"{message} ({detail})"
                self._recover_from_error(message)
                return
            if not result.transcription or not result.response:
                self._recover_from_error(
                    "AI pipeline returned an empty transcription or response."
                )
                return

            self._speak_response(result.response)
        finally:
            self._remove_temporary_file(recording_path)

    def _announce_offline(self) -> None:
        logger.warning("Internet is unavailable; skipping cloud AI requests.")
        self._speak_response(
            "Internet is unavailable. Please reconnect and try again."
        )

    def _last_ai_error(self) -> str | None:
        for component in (self.ai_pipeline.stt, self.ai_pipeline.llm):
            detail = getattr(component, "last_error", None)
            if detail:
                return str(detail)
        return None

    def _speak_response(self, response: str) -> None:
        if self._shutdown_event.is_set():
            return
        self._set_state(
            AssistantState.SPEAKING, "SPEAKING", DisplayStatus.SPEAKING
        )
        speech_path = self._new_temporary_file()
        generated_path: str | None = None
        try:
            generated_path = self.tts.save_to_file(response, str(speech_path))
            if not generated_path or not Path(generated_path).is_file():
                self._recover_from_error(
                    "eSpeak NG did not produce a speech audio file."
                )
                return
            if Path(generated_path).stat().st_size == 0:
                self._recover_from_error("eSpeak NG produced an empty audio file.")
                return

            if self._shutdown_event.is_set():
                return
            if self.hardware.speaker.is_playing:
                self.hardware.speaker.stop_playback()
            with self._shutdown_lock:
                if self._shutdown_complete:
                    return
                self.hardware.speaker.play_wav(generated_path)
            while self._running and self.hardware.speaker.is_playing:
                time.sleep(0.05)
            playback_error = getattr(
                self.hardware.speaker, "last_playback_error", None
            )
            if playback_error and not self._shutdown_event.is_set():
                self._recover_from_error(
                    f"Speaker playback failed: {playback_error}"
                )
        except Exception as exc:
            self._recover_from_error(f"Speech output failed: {exc}")
        finally:
            self._remove_temporary_file(speech_path)
            if generated_path:
                self._remove_temporary_file(Path(generated_path))

    def _has_usable_audio(self, filepath: Path) -> bool:
        try:
            with wave.open(str(filepath), "rb") as recording:
                if recording.getnframes() <= 0 or recording.getsampwidth() != 2:
                    return False
                while True:
                    frames = recording.readframes(8192)
                    if not frames:
                        return False
                    if any(frames):
                        return True
        except (OSError, EOFError, wave.Error):
            logger.warning("Microphone produced an invalid WAV recording.")
            return False

    def _new_temporary_file(self) -> Path:
        self.recording_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            suffix=".wav", prefix="vihaan-", dir=self.recording_dir, delete=False
        ) as temporary_file:
            path = Path(temporary_file.name)
        self._temporary_files.add(path)
        return path

    def _remove_temporary_file(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove temporary audio file: %s", path)
        finally:
            self._temporary_files.discard(path)

    def _cleanup_temporary_files(self) -> None:
        for path in tuple(self._temporary_files):
            self._remove_temporary_file(path)

    def _discard_queued_button_events(self) -> None:
        while True:
            try:
                self._events.get_nowait()
            except queue.Empty:
                return

    def _recover_from_error(self, message: str) -> None:
        logger.error("%s", message)
        if self._shutdown_event.is_set() or self.state == AssistantState.SHUTDOWN:
            return
        self._set_state(AssistantState.ERROR, "ERROR", DisplayStatus.ERROR)
        self._set_state(
            AssistantState.IDLE, "VIHAAN READY", DisplayStatus.IDLE
        )

    def _set_state(
        self,
        new_state: AssistantState,
        display_text: str | None = None,
        display_status: DisplayStatus | None = None,
    ) -> None:
        with self._shutdown_lock:
            if (
                new_state != AssistantState.SHUTDOWN
                and self._shutdown_event.is_set()
            ):
                return
            with self._state_lock:
                previous_state = self._state
                self._state = new_state
        if previous_state != new_state:
            logger.info("Assistant state: %s -> %s", previous_state.name, new_state.name)
        if display_text is not None or display_status is not None:
            self._update_display(display_text, display_status)

    def _update_display(
        self, text: str | None, status: DisplayStatus | None
    ) -> None:
        display = self.hardware.display
        if display is None:
            return
        try:
            if text is not None:
                display.show_text(text)
            if status is not None:
                display.show_status(status)
        except Exception:
            logger.warning("Optional display failed; continuing without it.", exc_info=True)
            self.hardware.display = None
