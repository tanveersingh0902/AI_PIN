"""Tests for the integrated assistant controller using simulated hardware."""

import time
from pathlib import Path
from threading import Event, Thread
from unittest.mock import MagicMock

import pytest

from ai.conversation import ConversationManager
from ai.llm import LLMClient
from ai.pipeline import AIPipeline, PipelineResult
from ai.speech_to_text import SpeechToText
from assistant.controller import AssistantController, AssistantState
from hardware.display import DisplayStatus
from hardware.factory import HardwareFactory
from hardware.microphone import MicrophoneInterface
from hardware.speaker import SpeakerInterface
from simulation.sim_button import SimButton
from simulation.sim_microphone import SimMicrophone
from simulation.sim_speaker import SimSpeaker
from utils.platform_detect import Platform


class FakeMicrophone(MicrophoneInterface):
    def __init__(self, audio=b"\x01\x00" * 1600, start_failure=None):
        self._recording = False
        self.audio = audio
        self.start_failure = start_failure
        self.started = 0
        self.stopped = 0
        self.cleaned = False

    @property
    def sample_rate(self):
        return 16000

    @property
    def channels(self):
        return 1

    @property
    def is_recording(self):
        return self._recording

    def start_recording(self):
        if self.start_failure:
            raise self.start_failure
        self.started += 1
        self._recording = True

    def stop_recording(self):
        self.stopped += 1
        self._recording = False
        return self.audio

    def record(self, _duration):
        del _duration
        return self.audio

    def cleanup(self):
        self.cleaned = True
        self._recording = False


class FakeSpeaker(SpeakerInterface):
    def __init__(self, failure=None):
        self.failure = failure
        self.async_failure = None
        self.last_playback_error = None
        self.played = []
        self.cleaned = False
        self._playing = False

    @property
    def is_playing(self):
        return self._playing

    def play_wav(self, filepath):
        if self.failure:
            raise self.failure
        if self.async_failure:
            self.last_playback_error = self.async_failure
            return
        self.last_playback_error = None
        self.played.append(filepath)

    def play_audio(self, _audio_data, _sample_rate=16000, _channels=1):
        del _audio_data, _sample_rate, _channels

    def stop_playback(self):
        self._playing = False

    def cleanup(self):
        self.cleaned = True


class FakeTTS:
    def __init__(self, produce_file=True):
        self.produce_file = produce_file
        self.spoken = []

    def save_to_file(self, text, filepath):
        self.spoken.append(text)
        if not self.produce_file:
            return ""
        Path(filepath).write_bytes(b"wav-data")
        return str(Path(filepath).resolve())


class FakePipeline:
    def __init__(self, result=None):
        self.result = result or PipelineResult(
            transcription="Hello", response="Hello there."
        )
        self.calls = []
        self.recording_existed_during_call = False

    def process_audio_file(self, filepath, speak=True):
        self.calls.append((filepath, speak))
        self.recording_existed_during_call = Path(filepath).is_file()
        return self.result


def make_controller(tmp_path, *, audio=b"\x01\x00" * 1600, result=None,
                    speaker_failure=None, produce_file=True):
    hardware = HardwareFactory.create(platform=Platform.WINDOWS)
    microphone = FakeMicrophone(audio)
    speaker = FakeSpeaker(speaker_failure)
    hardware.microphone = microphone
    hardware.speaker = speaker
    pipeline = FakePipeline(result)
    tts = FakeTTS(produce_file)
    controller = AssistantController(hardware, pipeline, tts, recording_dir=tmp_path)
    return controller, microphone, speaker, pipeline, tts


def wait_until(predicate, timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def start_controller(controller):
    thread = Thread(target=controller.run, daemon=True)
    thread.start()
    assert wait_until(lambda: controller.state == AssistantState.IDLE)
    return thread


def finish_controller(controller, thread):
    controller.stop()
    thread.join(timeout=2)
    assert not thread.is_alive()


def test_initialization_idle_and_graceful_shutdown(tmp_path):
    controller, microphone, speaker, _, _ = make_controller(tmp_path)
    assert controller.state == AssistantState.INITIALIZING
    thread = start_controller(controller)
    assert controller.state == AssistantState.IDLE

    finish_controller(controller, thread)

    assert controller.state == AssistantState.SHUTDOWN
    assert microphone.cleaned
    assert speaker.cleaned


def test_button_press_release_runs_complete_pipeline_once(tmp_path):
    controller, microphone, speaker, pipeline, tts = make_controller(tmp_path)
    thread = start_controller(controller)
    button = controller.hardware.button

    button.simulate_press()
    assert wait_until(lambda: controller.state == AssistantState.LISTENING)
    assert microphone.started == 1
    button.simulate_release()
    assert wait_until(
        lambda: controller.state == AssistantState.IDLE
        and bool(pipeline.calls)
    )

    assert microphone.stopped == 1
    assert pipeline.recording_existed_during_call
    assert pipeline.calls[0][1] is False
    assert tts.spoken == ["Hello there."]
    assert len(speaker.played) == 1
    assert list(tmp_path.iterdir()) == []
    finish_controller(controller, thread)


def test_repeated_press_events_do_not_start_multiple_recordings(tmp_path):
    controller, microphone, _, _, _ = make_controller(tmp_path)
    controller._set_state(AssistantState.IDLE)
    controller._handle_button_press()
    controller._handle_button_press()

    assert controller.state == AssistantState.LISTENING
    assert microphone.started == 1

    controller._handle_button_release()
    controller.shutdown()


def test_microphone_start_failure_recovers_to_idle(tmp_path):
    controller, microphone, _, _, _ = make_controller(tmp_path)
    microphone.start_failure = OSError("microphone unavailable")
    controller._set_state(AssistantState.IDLE)

    controller._handle_button_press()

    assert controller.state == AssistantState.IDLE
    assert microphone.started == 0
    controller.shutdown()


def test_button_initialization_failure_shuts_down_cleanly(tmp_path):
    class FailingButton(SimButton):
        def on_press(self, _callback):
            del _callback
            raise RuntimeError("button unavailable")

    controller, microphone, speaker, _, _ = make_controller(tmp_path)
    controller.hardware.button = FailingButton()

    assert controller.run() is False
    assert controller.state == AssistantState.SHUTDOWN
    assert microphone.cleaned
    assert speaker.cleaned


@pytest.mark.parametrize("audio", [b"", b"\x00\x00" * 1600, b"\x01"])
def test_empty_or_silent_recording_skips_ai(tmp_path, audio):
    controller, _, speaker, pipeline, _ = make_controller(tmp_path, audio=audio)
    controller._set_state(AssistantState.IDLE)

    controller._handle_button_press()
    controller._handle_button_release()

    assert pipeline.calls == []
    assert speaker.played == []
    assert controller.state == AssistantState.IDLE
    assert list(tmp_path.iterdir()) == []
    controller.shutdown()


def test_invalid_wav_recording_is_rejected_and_cleaned(tmp_path, monkeypatch):
    controller, microphone, speaker, pipeline, _ = make_controller(tmp_path)

    def write_invalid_wav(_audio, filepath):
        Path(filepath).write_bytes(b"not-a-wave-file")

    monkeypatch.setattr(microphone, "save_wav", write_invalid_wav)
    controller._set_state(AssistantState.IDLE)
    controller._handle_button_press()
    controller._handle_button_release()

    assert pipeline.calls == []
    assert speaker.played == []
    assert list(tmp_path.iterdir()) == []
    assert controller.state == AssistantState.IDLE
    controller.shutdown()


def test_ai_pipeline_failure_returns_to_idle_and_cleans_recording(tmp_path):
    failure = PipelineResult(error="STT failed")
    controller, _, speaker, pipeline, _ = make_controller(
        tmp_path, result=failure
    )
    controller._set_state(AssistantState.IDLE)

    controller._handle_button_press()
    controller._handle_button_release()

    assert pipeline.calls
    assert speaker.played == []
    assert controller.state == AssistantState.IDLE
    assert list(tmp_path.iterdir()) == []
    controller.shutdown()


def test_offline_assistant_skips_cloud_and_recovers_on_next_press(tmp_path):
    class NetworkStatus:
        def __init__(self, internet_available):
            self.internet_available = internet_available

    class Network:
        def __init__(self):
            self.results = [False, True]

        def check_status(self):
            return NetworkStatus(self.results.pop(0))

    controller, _, speaker, pipeline, tts = make_controller(tmp_path)
    controller.network_manager = Network()
    controller._set_state(AssistantState.IDLE)

    controller._handle_button_press()
    controller._handle_button_release()
    assert pipeline.calls == []
    assert tts.spoken == [
        "Internet is unavailable. Please reconnect and try again."
    ]
    assert len(speaker.played) == 1
    assert controller.state == AssistantState.IDLE

    controller._handle_button_press()
    controller._handle_button_release()
    assert len(pipeline.calls) == 1
    assert tts.spoken[-1] == "Hello there."
    assert len(speaker.played) == 2
    controller.shutdown()


def test_connection_lost_during_cloud_processing_uses_local_feedback(tmp_path):
    class NetworkStatus:
        def __init__(self, internet_available):
            self.internet_available = internet_available

    class Network:
        def __init__(self):
            self.results = [True, False]

        def check_status(self):
            return NetworkStatus(self.results.pop(0))

    controller, _, speaker, pipeline, tts = make_controller(
        tmp_path, result=PipelineResult(error="STT returned empty transcription.")
    )
    controller.network_manager = Network()
    controller._set_state(AssistantState.IDLE)

    controller._handle_button_press()
    controller._handle_button_release()

    assert len(pipeline.calls) == 1
    assert tts.spoken == [
        "Internet is unavailable. Please reconnect and try again."
    ]
    assert len(speaker.played) == 1
    assert controller.state == AssistantState.IDLE
    controller.shutdown()


def test_shutdown_during_processing_skips_speech_and_cleans_files(tmp_path):
    class BlockingPipeline:
        def __init__(self):
            self.started = Event()
            self.finish = Event()

        def process_audio_file(self, _filepath, speak=True):
            self.started.set()
            assert self.finish.wait(timeout=2)
            return PipelineResult(transcription="Hello", response="Goodbye.")

    controller, microphone, speaker, _, tts = make_controller(tmp_path)
    pipeline = BlockingPipeline()
    controller.ai_pipeline = pipeline
    controller._set_state(AssistantState.IDLE)
    controller._handle_button_press()

    worker = Thread(target=controller._handle_button_release)
    worker.start()
    assert pipeline.started.wait(timeout=2)
    assert list(tmp_path.glob("vihaan-*.wav"))

    controller.shutdown()
    assert not microphone.cleaned
    assert not speaker.cleaned
    pipeline.finish.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert controller.state == AssistantState.SHUTDOWN
    assert microphone.cleaned
    assert speaker.cleaned
    assert tts.spoken == []
    assert speaker.played == []
    assert list(tmp_path.iterdir()) == []


def test_controller_reports_expected_success_state_sequence(tmp_path):
    class Display:
        def __init__(self):
            self.statuses = []

        def show_text(self, _text):
            pass

        def show_status(self, status):
            self.statuses.append(status)

    controller, _, _, _, _ = make_controller(tmp_path)
    display = Display()
    controller.hardware.display = display
    controller._set_state(
        AssistantState.IDLE, "VIHAAN READY", DisplayStatus.IDLE
    )
    controller._handle_button_press()
    controller._handle_button_release()

    assert [status.value for status in display.statuses] == [
        "IDLE", "LISTENING", "THINKING", "SPEAKING", "IDLE"
    ]
    assert controller.state == AssistantState.IDLE
    controller.shutdown()


def test_tts_missing_or_playback_failure_is_recoverable(tmp_path):
    controller, _, speaker, _, _ = make_controller(
        tmp_path, produce_file=False
    )
    controller._set_state(AssistantState.IDLE)
    controller._handle_button_press()
    controller._handle_button_release()
    assert controller.state == AssistantState.IDLE
    assert speaker.played == []
    controller.shutdown()

    controller, _, speaker, _, _ = make_controller(
        tmp_path, speaker_failure=OSError("audio device unavailable")
    )
    controller._set_state(AssistantState.IDLE)
    controller._handle_button_press()
    controller._handle_button_release()
    assert controller.state == AssistantState.IDLE
    assert list(tmp_path.iterdir()) == []
    controller.shutdown()

    controller, _, speaker, _, _ = make_controller(tmp_path)
    speaker.async_failure = "simulated worker failure"
    controller._set_state(AssistantState.IDLE)
    controller._handle_button_press()
    controller._handle_button_release()
    assert controller.state == AssistantState.IDLE
    assert list(tmp_path.iterdir()) == []
    controller.shutdown()


def test_existing_ai_pipeline_updates_history_and_controller_uses_speaker(tmp_path):
    stt = SpeechToText(api_key="mock-key")
    stt._client = MagicMock()
    stt._client.audio.transcriptions.create.return_value = "What is VIHAAN?"
    llm = LLMClient(api_key="mock-key")
    llm._client = MagicMock()
    completion = MagicMock()
    completion.choices[0].message.content = "VIHAAN is a voice assistant."
    llm._client.chat.completions.create.return_value = completion
    tts = FakeTTS()
    conversation = ConversationManager("You are VIHAAN.")
    pipeline = AIPipeline(stt, llm, tts, conversation)

    hardware = HardwareFactory.create(platform=Platform.WINDOWS)
    hardware.microphone = FakeMicrophone()
    speaker = FakeSpeaker()
    hardware.speaker = speaker
    controller = AssistantController(hardware, pipeline, tts, tmp_path)
    controller._set_state(AssistantState.IDLE)

    controller._handle_button_press()
    controller._handle_button_release()

    assert stt._client.audio.transcriptions.create.call_count == 1
    assert llm._client.chat.completions.create.call_count == 1
    assert [message["role"] for message in conversation.get_history()] == [
        "user", "assistant"
    ]
    assert tts.spoken == ["VIHAAN is a voice assistant."]
    assert len(speaker.played) == 1
    assert list(tmp_path.iterdir()) == []
    controller.shutdown()


def test_windows_factory_uses_simulated_hardware():
    hardware = HardwareFactory.create(platform=Platform.WINDOWS)
    try:
        assert isinstance(hardware.microphone, SimMicrophone)
        assert isinstance(hardware.button, SimButton)
        assert isinstance(hardware.speaker, SimSpeaker)
    finally:
        hardware.cleanup()


def test_main_starts_with_windows_simulation_without_api_requests(monkeypatch):
    from dataclasses import replace

    import main as main_module

    monkeypatch.setattr(main_module, "setup_logging", lambda **kwargs: kwargs)
    monkeypatch.setattr(main_module, "detect_platform", lambda: Platform.WINDOWS)
    monkeypatch.setattr(
        main_module.signal, "signal", lambda *args: args[-1] if args else None
    )
    monkeypatch.setattr(
        main_module,
        "settings",
        replace(main_module.settings, GROQ_API_KEY="mock-key"),
    )

    captured = {}

    class StubNetworkManager:
        def __init__(self, **kwargs):
            captured["network_options"] = kwargs

        def diagnostics(self):
            return "mock network status"

    class StubAssistant:
        def __init__(
            self, hardware, ai_pipeline, tts, recording_dir, network_manager
        ):
            captured["hardware"] = hardware
            captured["ai_pipeline"] = ai_pipeline
            captured["tts"] = tts
            captured["recording_dir"] = recording_dir
            captured["network_manager"] = network_manager

        def run(self):
            return True

        def shutdown(self):
            captured["hardware"].cleanup()

    monkeypatch.setattr(main_module, "NetworkManager", StubNetworkManager)
    monkeypatch.setattr(main_module, "AssistantController", StubAssistant)

    assert main_module.main() == 0
    assert isinstance(captured["hardware"].microphone, SimMicrophone)
    assert isinstance(captured["hardware"].button, SimButton)
    assert isinstance(captured["hardware"].speaker, SimSpeaker)
    assert isinstance(captured["network_manager"], StubNetworkManager)


def test_main_missing_api_key_exits_before_network_or_hardware(monkeypatch):
    from dataclasses import replace

    import main as main_module

    monkeypatch.setattr(main_module, "setup_logging", lambda **kwargs: None)
    monkeypatch.setattr(main_module, "detect_platform", lambda: Platform.WINDOWS)
    monkeypatch.setattr(
        main_module,
        "settings",
        replace(main_module.settings, GROQ_API_KEY=""),
    )
    monkeypatch.setattr(
        main_module,
        "NetworkManager",
        lambda **_kwargs: pytest.fail("network should not be checked"),
    )
    monkeypatch.setattr(
        main_module.HardwareFactory,
        "create",
        lambda **_kwargs: pytest.fail("hardware should not be initialized"),
    )

    assert main_module.main() == 1
