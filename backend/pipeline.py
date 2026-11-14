"""
backend.pipeline — Voice Assistant Pipeline
=============================================
The central orchestrator.  It uses the HardwareFactory to get
platform-appropriate hardware, then ties together:

  1. Wake-word detection  →  activate
  2. Audio capture        →  raw bytes from mic
  3. Speech-to-Text       →  user's query as text
  4. LLM query            →  assistant's response text
  5. Text-to-Speech       →  spoken audio to speaker
  6. State transitions    →  LED / display feedback

The pipeline receives a HardwareKit from the factory — it never
imports hardware drivers directly.
"""

from __future__ import annotations

import logging
from utils.platform_detect import Platform
from hardware.factory import HardwareFactory, HardwareKit
from backend.state import StateManager

logger = logging.getLogger(__name__)


class VoiceAssistantPipeline:
    """
    Main voice assistant loop.

    TODO: Wire up AI components (STT, TTS, LLM, wake word) once
          the AI layer is implemented.
    """

    def __init__(self, platform: Platform = Platform.WINDOWS,
                 hardware: HardwareKit | None = None):
        self.platform = platform

        # Accept an injected HardwareKit, or create one via factory
        if hardware is not None:
            self.hw = hardware
        else:
            self.hw = HardwareFactory.create(platform=platform)

        self.state = StateManager()
        self._running = False
        logger.info("Pipeline created.")

    def _init_ai(self):
        """Instantiate AI engines (STT, TTS, LLM, wake word)."""
        # TODO: Wire up in Step 3 (AI integration)
        pass

    def run(self):
        """
        Start the assistant loop.

        Cycle: idle → wake → listen → think → speak → idle
        """
        self._running = True
        self._init_ai()

        logger.info("Pipeline running. Waiting for wake word …")

        while self._running:
            # Placeholder — will be implemented step by step:
            #
            # 1. Listen for wake word
            # 2. Capture user speech (microphone)
            # 3. STT → text
            # 4. LLM → response
            # 5. TTS → audio
            # 6. Play audio (speaker)
            #
            # For now, just block so the process stays alive.
            try:
                import time
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def shutdown(self):
        """Clean up all resources."""
        self._running = False
        self.hw.cleanup()
        logger.info("Pipeline shut down.")
