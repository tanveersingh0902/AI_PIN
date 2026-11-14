"""
ai.text_to_speech — eSpeak NG Text-to-Speech
===============================================
Converts text to spoken audio using the local `espeak-ng` system
executable.  No cloud API, no Python TTS library — just a
lightweight subprocess call.

eSpeak NG must be installed separately:
  - Windows : https://github.com/espeak-ng/espeak-ng/releases
  - Raspberry Pi : sudo apt install espeak-ng

This module does NOT play audio through speakers.  It either:
  1. Invokes espeak-ng to speak directly (uses system audio), or
  2. Saves speech to a WAV file for the hardware speaker layer.
"""

from __future__ import annotations

import shutil
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    eSpeak NG text-to-speech wrapper.

    Parameters
    ----------
    executable : str
        Name or path to the espeak-ng binary.
    voice : str
        Voice / language code (e.g., "en", "en-us", "hi").
    speed : int
        Words per minute (default 150).
    """

    def __init__(self, executable: str = "espeak-ng",
                 voice: str = "en", speed: int = 150):
        self._executable = executable
        self._voice = voice
        self._speed = speed
        logger.info(
            f"TextToSpeech: executable='{executable}', "
            f"voice='{voice}', speed={speed} wpm"
        )

    # ── Availability check ────────────────────────────────────

    def is_available(self) -> bool:
        """
        Check whether espeak-ng is installed and reachable.

        Returns
        -------
        bool
            True if the executable is found on the system PATH
            or at the configured path.
        """
        if shutil.which(self._executable):
            return True
        # Common Windows install path
        win_path = Path(r"C:\Program Files\eSpeak NG\espeak-ng.exe")
        if win_path.is_file():
            self._executable = str(win_path)
            return True
        return False

    # ── Speak directly ────────────────────────────────────────

    def speak(self, text: str) -> bool:
        """
        Speak text aloud using espeak-ng (blocks until finished).

        Parameters
        ----------
        text : str
            The text to speak.

        Returns
        -------
        bool
            True if speech completed successfully.
        """
        if not text or not text.strip():
            logger.warning("TTS: empty text, skipping.")
            return False

        if not self.is_available():
            logger.error("TTS: espeak-ng not found on this system.")
            return False

        cmd = [
            self._executable,
            "-v", self._voice,
            "-s", str(self._speed),
            "--", text,
        ]
        logger.debug(f"TTS cmd: {' '.join(cmd[:4])} '…'")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.error(f"TTS espeak-ng error: {result.stderr.strip()}")
                return False
            logger.info("TTS: speech completed.")
            return True

        except subprocess.TimeoutExpired:
            logger.error("TTS: espeak-ng timed out.")
            return False
        except FileNotFoundError:
            logger.error("TTS: espeak-ng executable not found.")
            return False
        except Exception as e:
            logger.error(f"TTS error: {type(e).__name__}: {e}")
            return False

    # ── Save to file ──────────────────────────────────────────

    def save_to_file(self, text: str, filepath: str) -> str:
        """
        Render speech to a WAV file (does not play it).

        Parameters
        ----------
        text : str
            The text to synthesise.
        filepath : str
            Destination WAV file path.

        Returns
        -------
        str
            The path to the saved file, or empty string on failure.
        """
        if not text or not text.strip():
            logger.warning("TTS: empty text, skipping.")
            return ""

        if not self.is_available():
            logger.error("TTS: espeak-ng not found on this system.")
            return ""

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self._executable,
            "-v", self._voice,
            "-s", str(self._speed),
            "-w", str(path),
            "--", text,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.error(f"TTS save error: {result.stderr.strip()}")
                return ""
            logger.info(f"TTS: saved speech to {path}")
            return str(path.resolve())

        except subprocess.TimeoutExpired:
            logger.error("TTS: espeak-ng timed out during save.")
            return ""
        except FileNotFoundError:
            logger.error("TTS: espeak-ng executable not found.")
            return ""
        except Exception as e:
            logger.error(f"TTS save error: {type(e).__name__}: {e}")
            return ""

    # ── Build command (for inspection / testing) ──────────────

    def build_command(self, text: str,
                      output_file: str | None = None) -> list[str]:
        """
        Return the espeak-ng command that would be executed.

        Useful for testing and debugging without running the process.
        """
        cmd = [
            self._executable,
            "-v", self._voice,
            "-s", str(self._speed),
        ]
        if output_file:
            cmd.extend(["-w", output_file])
        cmd.extend(["--", text])
        return cmd
