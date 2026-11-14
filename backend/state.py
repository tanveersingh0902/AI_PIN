"""
backend.state — Device State Machine
======================================
Tracks the current state of the voice assistant to coordinate
LED feedback, audio routing, and user interaction.

States
------
  IDLE       : Waiting for wake word (LED off or dim pulse)
  LISTENING  : Capturing user speech (LED solid on)
  THINKING   : Waiting for LLM response (LED blinking)
  SPEAKING   : Playing TTS audio (LED solid on)
  ERROR      : Something went wrong (LED rapid blink)
  OFFLINE    : No internet — limited functionality
"""

import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class DeviceState(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    ERROR = auto()
    OFFLINE = auto()


class StateManager:
    """
    Simple state machine for the device.

    TODO: Add observer pattern so LED / UI reacts to state changes.
    """

    def __init__(self):
        self._state = DeviceState.IDLE
        logger.info(f"Initial state: {self._state.name}")

    @property
    def state(self) -> DeviceState:
        return self._state

    def transition(self, new_state: DeviceState) -> None:
        """
        Move to a new state with logging.

        Parameters
        ----------
        new_state : DeviceState
            The state to transition to.
        """
        old = self._state
        self._state = new_state
        logger.info(f"State: {old.name} → {new_state.name}")

    def is_idle(self) -> bool:
        return self._state == DeviceState.IDLE

    def is_busy(self) -> bool:
        return self._state in (
            DeviceState.LISTENING,
            DeviceState.THINKING,
            DeviceState.SPEAKING,
        )
