"""
ai.pipeline — AI Pipeline Orchestrator
========================================
Connects the three AI components into a single processing flow:

    Audio file
        ↓
    Groq Whisper STT   (cloud)
        ↓
    Transcribed text
        ↓
    Groq LLM           (cloud)
        ↓
    Generated response
        ↓
    eSpeak NG TTS      (local)
        ↓
    Spoken response

Each component is injected via the constructor so they can be
independently tested and mocked.

This module does NOT access GPIO or physical hardware directly.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from ai.speech_to_text import SpeechToText
from ai.llm import LLMClient
from ai.text_to_speech import TextToSpeech
from ai.conversation import ConversationManager

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a single pipeline run."""
    transcription: str = ""
    response: str = ""
    spoken: bool = False
    error: Optional[str] = None


class AIPipeline:
    """
    Orchestrates STT → LLM → TTS for a single user interaction.

    Parameters
    ----------
    stt : SpeechToText
        Groq Whisper STT client.
    llm : LLMClient
        Groq LLM chat client.
    tts : TextToSpeech
        eSpeak NG TTS wrapper.
    conversation : ConversationManager
        Manages multi-turn conversation history.
    """

    def __init__(self, stt: SpeechToText, llm: LLMClient,
                 tts: TextToSpeech, conversation: ConversationManager):
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.conversation = conversation
        logger.info("AIPipeline initialised.")

    # ── Main pipeline ─────────────────────────────────────────

    def process_audio_file(self, audio_filepath: str,
                           speak: bool = True) -> PipelineResult:
        """
        Run the full pipeline: audio file → STT → LLM → TTS.

        Parameters
        ----------
        audio_filepath : str
            Path to the recorded audio file (WAV).
        speak : bool
            If True, speak the response aloud via TTS.

        Returns
        -------
        PipelineResult
            Contains the transcription, LLM response, and status.
        """
        result = PipelineResult()

        # ── Step 1: Speech-to-Text ────────────────────────────
        logger.info("Pipeline Step 1/3: Speech-to-Text …")
        try:
            result.transcription = self.stt.transcribe_file(audio_filepath)
        except Exception as e:
            result.error = f"STT failed: {e}"
            logger.error(result.error)
            return result

        if not result.transcription:
            result.error = "STT returned empty transcription."
            logger.warning(result.error)
            return result

        # ── Step 2: LLM Query ────────────────────────────────
        logger.info("Pipeline Step 2/3: LLM query …")
        try:
            result.response = self.llm.query(
                result.transcription,
                conversation_history=self.conversation.get_history(),
            )
        except Exception as e:
            result.error = f"LLM failed: {e}"
            logger.error(result.error)
            return result

        if not result.response:
            result.error = "LLM returned empty response."
            logger.warning(result.error)
            return result

        self.conversation.add_user_message(result.transcription)
        self.conversation.add_assistant_message(result.response)

        # ── Step 3: Text-to-Speech ────────────────────────────
        if speak:
            logger.info("Pipeline Step 3/3: Text-to-Speech …")
            try:
                result.spoken = self.tts.speak(result.response)
            except Exception as e:
                logger.warning(f"TTS failed (non-fatal): {e}")
                result.spoken = False
        else:
            logger.info("Pipeline Step 3/3: TTS skipped (speak=False).")

        logger.info("Pipeline complete.")
        return result

    def process_audio_bytes(self, audio_data: bytes,
                            speak: bool = True) -> PipelineResult:
        """
        Run the full pipeline: raw audio bytes → STT → LLM → TTS.

        Parameters
        ----------
        audio_data : bytes
            Audio content (WAV format with headers).
        speak : bool
            If True, speak the response aloud via TTS.

        Returns
        -------
        PipelineResult
        """
        result = PipelineResult()

        # ── Step 1: Speech-to-Text ────────────────────────────
        logger.info("Pipeline Step 1/3: Speech-to-Text (bytes) …")
        try:
            result.transcription = self.stt.transcribe_bytes(audio_data)
        except Exception as e:
            result.error = f"STT failed: {e}"
            logger.error(result.error)
            return result

        if not result.transcription:
            result.error = "STT returned empty transcription."
            logger.warning(result.error)
            return result

        # ── Step 2: LLM Query ────────────────────────────────
        logger.info("Pipeline Step 2/3: LLM query …")
        try:
            result.response = self.llm.query(
                result.transcription,
                conversation_history=self.conversation.get_history(),
            )
        except Exception as e:
            result.error = f"LLM failed: {e}"
            logger.error(result.error)
            return result

        if not result.response:
            result.error = "LLM returned empty response."
            logger.warning(result.error)
            return result

        self.conversation.add_user_message(result.transcription)
        self.conversation.add_assistant_message(result.response)

        # ── Step 3: Text-to-Speech ────────────────────────────
        if speak:
            logger.info("Pipeline Step 3/3: Text-to-Speech …")
            try:
                result.spoken = self.tts.speak(result.response)
            except Exception as e:
                logger.warning(f"TTS failed (non-fatal): {e}")
                result.spoken = False

        logger.info("Pipeline complete.")
        return result

    # ── Utility ───────────────────────────────────────────────

    def clear_history(self) -> None:
        """Reset conversation history."""
        self.conversation.clear()
