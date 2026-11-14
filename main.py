"""VIHAAN AI PIN application entry point."""

import logging
import signal

from ai.conversation import ConversationManager
from ai.llm import LLMClient
from ai.pipeline import AIPipeline
from ai.speech_to_text import SpeechToText
from ai.text_to_speech import TextToSpeech
from assistant.controller import AssistantController
from config import CACHE_DIR, settings
from hardware.factory import HardwareFactory, HardwareKit
from utils.logger import setup_logging
from utils.platform_detect import detect_platform


def _handle_shutdown_signal(_signum, _frame) -> None:
    del _signum, _frame
    raise KeyboardInterrupt


def main() -> int:
    setup_logging(level=settings.LOG_LEVEL)
    logger = logging.getLogger("vihaan")
    platform = detect_platform()
    logger.info("Platform detected: %s", platform.value)
    logger.info("%s v%s", settings.PROJECT_NAME, settings.VERSION)

    signal.signal(signal.SIGINT, _handle_shutdown_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_shutdown_signal)

    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY is missing. Set it in the environment or .env.")
        return 1

    hardware: HardwareKit | None = None
    assistant: AssistantController | None = None
    try:
        hardware = HardwareFactory.create(
            platform=platform,
            sample_rate=settings.AUDIO_SAMPLE_RATE,
            channels=settings.AUDIO_CHANNELS,
            chunk_size=settings.AUDIO_CHUNK_SIZE,
            button_pin=settings.BUTTON_GPIO_PIN,
            enable_display=True,
            enable_camera=False,
        )

        stt = SpeechToText(
            api_key=settings.GROQ_API_KEY,
            model="whisper-large-v3-turbo",
            timeout=settings.GROQ_TIMEOUT,
        )
        llm = LLMClient(
            api_key=settings.GROQ_API_KEY,
            model="openai/gpt-oss-120b",
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            timeout=settings.GROQ_TIMEOUT,
            system_prompt=settings.LLM_SYSTEM_PROMPT,
        )
        tts = TextToSpeech(
            executable=settings.ESPEAK_EXECUTABLE,
            voice=settings.ESPEAK_VOICE,
            speed=settings.ESPEAK_SPEED,
        )
        conversation = ConversationManager(
            system_prompt=settings.LLM_SYSTEM_PROMPT,
            max_turns=settings.CONVERSATION_MAX_TURNS,
        )
        ai_pipeline = AIPipeline(stt, llm, tts, conversation)
        assistant = AssistantController(
            hardware=hardware,
            ai_pipeline=ai_pipeline,
            tts=tts,
            recording_dir=CACHE_DIR,
        )
        return 0 if assistant.run() else 1
    except KeyboardInterrupt:
        logger.info("Interrupted; shutting down.")
        return 0
    except Exception:
        logger.exception("VIHAAN could not start or stopped unexpectedly.")
        return 1
    finally:
        if assistant is not None:
            assistant.shutdown()
        elif hardware is not None:
            hardware.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
