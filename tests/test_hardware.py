"""
tests.test_hardware — Hardware Abstraction Tests
==================================================
Tests that run on Windows using the simulated hardware layer.
Verifies interfaces, the factory, and all simulation implementations.

Run with:  pytest tests/test_hardware.py -v
"""

import os
import sys
import time
import wave
import threading
import tempfile
from types import SimpleNamespace
import pytest

from utils.platform_detect import Platform
from hardware.display import DisplayStatus


# ═══════════════════════════════════════════════════════════════
#  INTERFACE TESTS
# ═══════════════════════════════════════════════════════════════

class TestInterfaces:
    """Verify that all ABCs are importable and well-formed."""

    def test_microphone_interface_exists(self):
        from hardware.microphone import MicrophoneInterface
        assert hasattr(MicrophoneInterface, "start_recording")
        assert hasattr(MicrophoneInterface, "stop_recording")
        assert hasattr(MicrophoneInterface, "record")
        assert hasattr(MicrophoneInterface, "save_wav")
        assert hasattr(MicrophoneInterface, "cleanup")

    def test_speaker_interface_exists(self):
        from hardware.speaker import SpeakerInterface
        assert hasattr(SpeakerInterface, "play_wav")
        assert hasattr(SpeakerInterface, "play_audio")
        assert hasattr(SpeakerInterface, "stop_playback")
        assert hasattr(SpeakerInterface, "cleanup")

    def test_button_interface_exists(self):
        from hardware.button import ButtonInterface
        assert hasattr(ButtonInterface, "is_pressed")
        assert hasattr(ButtonInterface, "on_press")
        assert hasattr(ButtonInterface, "on_release")
        assert hasattr(ButtonInterface, "wait_for_press")
        assert hasattr(ButtonInterface, "cleanup")

    def test_display_interface_exists(self):
        from hardware.display import DisplayInterface
        assert hasattr(DisplayInterface, "init")
        assert hasattr(DisplayInterface, "show_text")
        assert hasattr(DisplayInterface, "show_status")
        assert hasattr(DisplayInterface, "clear")
        assert hasattr(DisplayInterface, "cleanup")

    def test_camera_interface_exists(self):
        from hardware.camera import CameraInterface
        assert hasattr(CameraInterface, "is_available")
        assert hasattr(CameraInterface, "capture_image")
        assert hasattr(CameraInterface, "cleanup")

    def test_sim_camera_implements_camera_interface(self):
        from hardware.camera import CameraInterface
        from simulation.sim_camera import SimCamera

        camera = SimCamera()
        assert isinstance(camera, CameraInterface)
        assert camera.capture_image("unused.jpg") == ""


def test_helpers_import_without_linux_resource_module(monkeypatch):
    import importlib
    import sys

    monkeypatch.setattr(sys, "platform", "win32")
    helpers = importlib.import_module("utils.helpers")
    assert helpers.get_memory_usage_mb() == 0.0

    def test_display_status_enum(self):
        assert DisplayStatus.IDLE.value == "IDLE"
        assert DisplayStatus.LISTENING.value == "LISTENING"
        assert DisplayStatus.THINKING.value == "THINKING"
        assert DisplayStatus.SPEAKING.value == "SPEAKING"
        assert DisplayStatus.ERROR.value == "ERROR"


# ═══════════════════════════════════════════════════════════════
#  SIMULATED MICROPHONE TESTS
# ═══════════════════════════════════════════════════════════════

class TestSimMicrophone:
    """Test SimMicrophone (silence mode — no PyAudio dependency)."""

    def _make_mic(self):
        from simulation.sim_microphone import SimMicrophone
        mic = SimMicrophone(sample_rate=16000, channels=1, chunk_size=1024)
        # Force silence mode so tests don't need PyAudio
        if mic._audio is not None:
            mic._audio.terminate()
            mic._audio = None
        return mic

    def test_properties(self):
        mic = self._make_mic()
        assert mic.sample_rate == 16000
        assert mic.channels == 1
        assert mic.is_recording is False
        mic.cleanup()

    def test_record_fixed_duration(self):
        mic = self._make_mic()
        audio = mic.record(duration=0.5)
        # 0.5s × 16000 Hz × 2 bytes × 1 ch = 16000 bytes
        expected = int(16000 * 0.5) * 2 * 1
        assert len(audio) == expected
        assert isinstance(audio, bytes)
        mic.cleanup()

    def test_start_stop_recording(self):
        mic = self._make_mic()
        mic.start_recording()
        assert mic.is_recording is True
        time.sleep(0.3)
        audio = mic.stop_recording()
        assert mic.is_recording is False
        assert len(audio) > 0
        mic.cleanup()

    def test_save_wav(self):
        mic = self._make_mic()
        audio = mic.record(duration=0.25)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            result = mic.save_wav(audio, path)
            assert os.path.isfile(result)
            # Verify the WAV is valid
            with wave.open(result, "rb") as wf:
                assert wf.getnchannels() == 1
                assert wf.getsampwidth() == 2
                assert wf.getframerate() == 16000
                assert wf.getnframes() > 0
        finally:
            os.unlink(path)
            mic.cleanup()

    def test_double_start_ignored(self):
        mic = self._make_mic()
        mic.start_recording()
        mic.start_recording()  # Should log warning, not crash
        assert mic.is_recording is True
        mic.stop_recording()
        mic.cleanup()

    def test_stop_without_start(self):
        mic = self._make_mic()
        audio = mic.stop_recording()
        assert audio == b""
        mic.cleanup()


# ═══════════════════════════════════════════════════════════════
#  SIMULATED SPEAKER TESTS
# ═══════════════════════════════════════════════════════════════

class TestSimSpeaker:
    """Test SimSpeaker (log-only fallback mode)."""

    def _make_speaker(self):
        from simulation.sim_speaker import SimSpeaker
        spk = SimSpeaker()
        return spk

    def test_initial_state(self):
        spk = self._make_speaker()
        assert spk.is_playing is False
        spk.cleanup()

    def test_play_missing_file(self):
        spk = self._make_speaker()
        spk.play_wav("/nonexistent/file.wav")
        # Should log error, not crash
        assert spk.is_playing is False
        spk.cleanup()

    def test_play_wav_valid_file(self):
        """Create a tiny WAV and play it (may be log-only)."""
        spk = self._make_speaker()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            # Write a minimal valid WAV
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00" * 3200)
            spk.play_wav(path)
            time.sleep(0.2)
            spk.stop_playback()
            assert spk.is_playing is False
        finally:
            os.unlink(path)
            spk.cleanup()

    def test_play_raw_audio(self):
        spk = self._make_speaker()
        spk.play_audio(b"\x00" * 3200, sample_rate=16000, channels=1)
        time.sleep(0.1)
        spk.stop_playback()
        assert spk.is_playing is False
        spk.cleanup()

    def test_stop_when_not_playing(self):
        spk = self._make_speaker()
        spk.stop_playback()  # Should not crash
        spk.cleanup()


def test_pi_speaker_worker_reports_failure_and_closes_stream(tmp_path, monkeypatch):
    from hardware.speaker import PiSpeaker

    class FakeStream:
        def __init__(self):
            self.closed = threading.Event()
            self.stopped = False

        def write(self, _data):
            raise OSError("simulated device failure")

        def stop_stream(self):
            self.stopped = True

        def close(self):
            self.closed.set()

    class FakeAudio:
        def __init__(self, stream):
            self.stream = stream

        def get_format_from_width(self, _width):
            return 1

        def open(self, **_kwargs):
            return self.stream

        def terminate(self):
            pass

    stream = FakeStream()
    speaker = PiSpeaker()
    speaker._audio = FakeAudio(stream)
    monkeypatch.setitem(sys.modules, "pyaudio", SimpleNamespace())
    wav_path = tmp_path / "failure.wav"
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x01\x00" * 16)

    speaker.play_wav(str(wav_path))

    assert stream.closed.wait(timeout=2)
    if speaker._play_thread is not None:
        speaker._play_thread.join(timeout=2)
    assert stream.stopped
    assert speaker.last_playback_error is not None
    assert "OSError" in speaker.last_playback_error
    assert speaker.is_playing is False
    speaker.cleanup()


# ═══════════════════════════════════════════════════════════════
#  SIMULATED BUTTON TESTS
# ═══════════════════════════════════════════════════════════════

class TestSimButton:
    """Test SimButton programmatic triggers."""

    def _make_button(self):
        from simulation.sim_button import SimButton
        return SimButton()

    def test_initial_state(self):
        btn = self._make_button()
        assert btn.is_pressed() is False
        btn.cleanup()

    def test_simulate_press_release(self):
        btn = self._make_button()
        btn.simulate_press()
        assert btn.is_pressed() is True
        btn.simulate_release()
        assert btn.is_pressed() is False
        btn.cleanup()

    def test_press_callback(self):
        btn = self._make_button()
        results = []
        btn.on_press(lambda: results.append("pressed"))
        btn.simulate_press()
        assert results == ["pressed"]
        btn.cleanup()

    def test_release_callback(self):
        btn = self._make_button()
        results = []
        btn.on_release(lambda: results.append("released"))
        btn.simulate_release()
        assert results == ["released"]
        btn.cleanup()

    def test_press_and_release_callbacks(self):
        btn = self._make_button()
        events = []
        btn.on_press(lambda: events.append("P"))
        btn.on_release(lambda: events.append("R"))
        btn.simulate_press()
        btn.simulate_release()
        assert events == ["P", "R"]
        btn.cleanup()

    def test_wait_for_press_with_simulate(self):
        btn = self._make_button()
        # Simulate press from another thread after a short delay
        def delayed_press():
            time.sleep(0.1)
            btn.simulate_press()
        t = threading.Thread(target=delayed_press, daemon=True)
        t.start()
        result = btn.wait_for_press(timeout=2.0)
        assert result is True
        btn.cleanup()

    def test_wait_for_press_timeout(self):
        btn = self._make_button()
        result = btn.wait_for_press(timeout=0.1)
        assert result is False
        btn.cleanup()


# ═══════════════════════════════════════════════════════════════
#  SIMULATED DISPLAY TESTS
# ═══════════════════════════════════════════════════════════════

class TestSimDisplay:
    """Test SimDisplay console output."""

    def _make_display(self):
        from simulation.sim_display import SimDisplay
        d = SimDisplay()
        d.init()
        return d

    def test_init(self):
        d = self._make_display()
        assert d.width == 128
        assert d.height == 160
        d.cleanup()

    def test_show_text(self):
        d = self._make_display()
        d.show_text("Hello VIHAAN", line=0)
        assert d._lines[0] == "Hello VIHAAN"
        d.show_text("Line 2", line=1)
        assert d._lines[1] == "Line 2"
        d.cleanup()

    def test_show_all_statuses(self):
        d = self._make_display()
        for status in DisplayStatus:
            d.show_status(status)
            assert d._status == status
        d.cleanup()

    def test_clear(self):
        d = self._make_display()
        d.show_text("Something", line=0)
        d.clear()
        assert d._lines[0] == ""
        d.cleanup()

    def test_brightness(self):
        d = self._make_display()
        d.set_brightness(128)
        assert d._brightness == 128
        d.set_brightness(999)  # Should clamp to 255
        assert d._brightness == 255
        d.set_brightness(-10)  # Should clamp to 0
        assert d._brightness == 0
        d.cleanup()


# ═══════════════════════════════════════════════════════════════
#  HARDWARE FACTORY TESTS
# ═══════════════════════════════════════════════════════════════

class TestHardwareFactory:
    """Test that the factory creates the right implementations."""

    def test_create_sim_kit(self):
        from hardware.factory import HardwareFactory, HardwareKit
        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        assert isinstance(kit, HardwareKit)
        assert kit.platform == Platform.WINDOWS
        assert kit.microphone is not None
        assert kit.speaker is not None
        assert kit.button is not None
        kit.cleanup()

    def test_pi_can_force_simulation_without_initializing_pi_drivers(
        self, monkeypatch
    ):
        from hardware.factory import HardwareFactory
        from simulation import sim_microphone, sim_speaker
        from simulation.sim_button import SimButton
        from simulation.sim_microphone import SimMicrophone
        from simulation.sim_speaker import SimSpeaker

        monkeypatch.setattr(sim_microphone, "_HAS_PYAUDIO", False)
        monkeypatch.setattr(sim_microphone, "_pa", None, raising=False)
        monkeypatch.setattr(sim_speaker, "_HAS_PYAUDIO", False)
        monkeypatch.setattr(sim_speaker, "_HAS_WINSOUND", False)
        monkeypatch.setattr(
            HardwareFactory,
            "_create_pi",
            staticmethod(
                lambda *_args, **_kwargs: pytest.fail(
                    "Pi drivers must not initialize in simulation mode."
                )
            ),
        )

        kit = HardwareFactory.create(
            platform=Platform.RASPBERRY_PI,
            hardware_mode="simulation",
            enable_display=False,
        )
        try:
            assert kit.platform == Platform.RASPBERRY_PI
            assert isinstance(kit.microphone, SimMicrophone)
            assert isinstance(kit.speaker, SimSpeaker)
            assert isinstance(kit.button, SimButton)
            assert kit.display is None
        finally:
            kit.cleanup()

    def test_invalid_hardware_mode_is_rejected(self):
        from hardware.factory import HardwareFactory

        with pytest.raises(ValueError, match="hardware_mode"):
            HardwareFactory.create(
                platform=Platform.RASPBERRY_PI,
                hardware_mode="unknown",
            )

    def test_sim_kit_has_display(self):
        from hardware.factory import HardwareFactory
        kit = HardwareFactory.create(
            platform=Platform.WINDOWS, enable_display=True
        )
        assert kit.display is not None
        kit.cleanup()

    def test_sim_kit_no_display(self):
        from hardware.factory import HardwareFactory
        kit = HardwareFactory.create(
            platform=Platform.WINDOWS, enable_display=False
        )
        assert kit.display is None
        kit.cleanup()

    def test_sim_kit_no_camera(self):
        from hardware.factory import HardwareFactory
        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        assert kit.camera is None
        kit.cleanup()

    def test_sim_mic_is_correct_type(self):
        from hardware.factory import HardwareFactory
        from hardware.microphone import MicrophoneInterface
        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        assert isinstance(kit.microphone, MicrophoneInterface)
        kit.cleanup()

    def test_sim_speaker_is_correct_type(self):
        from hardware.factory import HardwareFactory
        from hardware.speaker import SpeakerInterface
        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        assert isinstance(kit.speaker, SpeakerInterface)
        kit.cleanup()

    def test_sim_button_is_correct_type(self):
        from hardware.factory import HardwareFactory
        from hardware.button import ButtonInterface
        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        assert isinstance(kit.button, ButtonInterface)
        kit.cleanup()

    def test_sim_display_is_correct_type(self):
        from hardware.factory import HardwareFactory
        from hardware.display import DisplayInterface
        kit = HardwareFactory.create(
            platform=Platform.WINDOWS, enable_display=True
        )
        assert isinstance(kit.display, DisplayInterface)
        kit.cleanup()

    def test_custom_sample_rate(self):
        from hardware.factory import HardwareFactory
        kit = HardwareFactory.create(
            platform=Platform.WINDOWS, sample_rate=8000
        )
        assert kit.microphone.sample_rate == 8000
        kit.cleanup()

    def test_pi_platform_falls_back_gracefully(self):
        """On Windows, requesting Pi hardware should fall back to sim."""
        from hardware.factory import HardwareFactory
        kit = HardwareFactory.create(platform=Platform.RASPBERRY_PI)
        # Should not crash — falls back to sim for each component
        assert kit.microphone is not None
        assert kit.speaker is not None
        assert kit.button is not None
        kit.cleanup()

    def test_cleanup_is_idempotent(self):
        from hardware.factory import HardwareFactory
        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        kit.cleanup()
        kit.cleanup()  # Second cleanup should not crash


# ═══════════════════════════════════════════════════════════════
#  INTEGRATION: FACTORY + PIPELINE
# ═══════════════════════════════════════════════════════════════

class TestPipelineIntegration:
    """Verify pipeline works with factory-created hardware."""

    def test_pipeline_with_sim_hardware(self):
        from hardware.factory import HardwareFactory
        from backend.pipeline import VoiceAssistantPipeline

        kit = HardwareFactory.create(platform=Platform.WINDOWS)
        pipeline = VoiceAssistantPipeline(
            platform=Platform.WINDOWS, hardware=kit
        )
        assert pipeline.hw is kit
        assert pipeline._running is False
        pipeline.shutdown()

    def test_pipeline_default_creates_hardware(self):
        from backend.pipeline import VoiceAssistantPipeline

        pipeline = VoiceAssistantPipeline(platform=Platform.WINDOWS)
        assert pipeline.hw is not None
        assert pipeline.hw.microphone is not None
        pipeline.shutdown()
