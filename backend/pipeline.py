"""
backend.pipeline — Voice Assistant Pipeline
=============================================
The central orchestrator. It ties together:
  1. Wake-word detection  →  activate
  2. Audio capture        →  raw bytes from mic
  3. Speech-to-Text       →  user's query as text
  4. LLM query            →  assistant's response text
  5. Text-to-Speech       →  spoken audio to speaker
  6. State transitions    →  LED / UI feedback

The pipeline selects real or simulated hardware drivers based on
the detected platform.
"""

import logging
from utils.platform_detect import Platform

logger = logging.getLogger(__name__)


class VoiceAssistantPipeline:
    """
    Main voice assistant loop.

    TODO: Wire up all components once individual modules are implemented.
    """

    def __init__(self, platform: Platform = Platform.WINDOWS):
        self.platform = platform
        self._running = False
        logger.info("Pipeline created.")

    def _init_hardware(self):
        """
        Instantiate hardware drivers.
        Uses simulation/ on Windows, hardware/ on Raspberry Pi.
        """
        if self.platform == Platform.RASPBERRY_PI:
            logger.info("Loading real hardware drivers …")
            # from hardware.mic import Microphone
            # from hardware.speaker import Speaker
            # from hardware.button import Button
            # from hardware.led import LED
        else:
            logger.info("Loading simulated hardware drivers …")
            # from simulation.sim_mic import SimMicrophone
            # from simulation.sim_speaker import SimSpeaker
            # from simulation.sim_button import SimButton
            # from simulation.sim_led import SimLED

    def _init_ai(self):
        """Instantiate AI engines (STT, TTS, LLM, wake word)."""
        # from ai.stt import SpeechToText
        # from ai.tts import TextToSpeech
        # from ai.llm import LLMClient
        # from ai.wake_word import WakeWordDetector
        pass

    def run(self):
        """
        Start the assistant loop.

        Cycle: idle → wake → listen → think → speak → idle
        """
        self._running = True
        self._init_hardware()
        self._init_ai()

        logger.info("Pipeline running. Waiting for wake word …")

        while self._running:
            # Placeholder — will be implemented step by step:
            #
            # 1. Listen for wake word
            # 2. Capture user speech
            # 3. STT → text
            # 4. LLM → response
            # 5. TTS → audio
            # 6. Play audio
            #
            # For now, just block so the process stays alive.
            try:
                import time
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def shutdown(self):
        """Clean up resources."""
        self._running = False
        logger.info("Pipeline shut down.")
