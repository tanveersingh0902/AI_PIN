"""
simulation.sim_display — Simulated Display
=============================================
Drop-in replacement for PiDisplay on Windows / dev machines.

Renders all display output to the console with formatted logging
and emoji indicators — no physical display or graphics library
required.

Implements hardware.display.DisplayInterface.
"""

import logging
from hardware.display import DisplayInterface, DisplayStatus

logger = logging.getLogger(__name__)


# Status → emoji mapping for terminal output
_STATUS_EMOJI = {
    DisplayStatus.IDLE:      "⚪ IDLE      ",
    DisplayStatus.LISTENING: "🟢 LISTENING ",
    DisplayStatus.THINKING:  "🟡 THINKING  ",
    DisplayStatus.SPEAKING:  "🔵 SPEAKING  ",
    DisplayStatus.ERROR:     "🔴 ERROR     ",
}


class SimDisplay(DisplayInterface):
    """
    Simulated display for Windows development.

    Prints display content to the terminal with visual formatting.
    Maintains an internal text buffer so show_text() / clear()
    behave consistently.
    """

    MAX_LINES = 8  # Simulated screen has 8 text lines

    def __init__(self, width: int = 128, height: int = 160):
        self.width = width
        self.height = height
        self._lines: list[str] = [""] * self.MAX_LINES
        self._status: DisplayStatus = DisplayStatus.IDLE
        self._brightness = 255

    def init(self) -> None:
        logger.info(
            f"SimDisplay: virtual {self.width}×{self.height} display ready."
        )

    def show_text(self, text: str, line: int = 0) -> None:
        if 0 <= line < self.MAX_LINES:
            self._lines[line] = text
        logger.info(f"📺 DISPLAY [{line}]: {text}")

    def show_status(self, status: DisplayStatus) -> None:
        self._status = status
        label = _STATUS_EMOJI.get(status, status.value)
        logger.info(f"📺 DISPLAY STATUS → {label}")

    def clear(self) -> None:
        self._lines = [""] * self.MAX_LINES
        logger.info("📺 DISPLAY: cleared")

    def set_brightness(self, level: int) -> None:
        self._brightness = max(0, min(255, level))
        logger.debug(f"SimDisplay: brightness → {self._brightness}/255")

    def cleanup(self) -> None:
        self.clear()
        logger.info("SimDisplay: cleaned up.")
