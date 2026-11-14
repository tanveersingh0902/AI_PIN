"""
tests.test_pipeline — Pipeline Tests
======================================
Basic smoke tests for the voice assistant pipeline.
"""

from backend.pipeline import VoiceAssistantPipeline
from backend.state import DeviceState, StateManager
from backend.session import Session
from utils.platform_detect import Platform


def test_pipeline_creation():
    """Pipeline should instantiate without errors."""
    pipeline = VoiceAssistantPipeline(platform=Platform.WINDOWS)
    assert pipeline.platform == Platform.WINDOWS
    assert pipeline._running is False


def test_state_transitions():
    """StateManager should track transitions correctly."""
    sm = StateManager()
    assert sm.state == DeviceState.IDLE
    assert sm.is_idle()

    sm.transition(DeviceState.LISTENING)
    assert sm.state == DeviceState.LISTENING
    assert sm.is_busy()

    sm.transition(DeviceState.THINKING)
    assert sm.state == DeviceState.THINKING
    assert sm.is_busy()

    sm.transition(DeviceState.IDLE)
    assert sm.is_idle()


def test_session_history():
    """Session should store and trim conversation history."""
    session = Session(max_turns=3)
    session.add_turn("user", "Hello")
    session.add_turn("assistant", "Hi there!")
    assert len(session.history) == 2

    session.clear()
    assert len(session.history) == 0
