"""
tests.test_ai — AI Pipeline Tests (Fully Mocked)
==================================================
All tests run WITHOUT:
  - Internet access
  - Groq API credits
  - Physical hardware
  - eSpeak NG installed

Every external dependency is mocked.

Run with:  pytest tests/test_ai.py -v
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock


# ═══════════════════════════════════════════════════════════════
#  1. CONFIGURATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestConfiguration:
    """Test that config.py loads Groq/eSpeak settings correctly."""

    def test_groq_api_key_from_env(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123"}):
            # Settings reads os.getenv at construction time
            from config import Settings
            s = Settings(GROQ_API_KEY=os.environ["GROQ_API_KEY"])
            assert s.GROQ_API_KEY == "test-key-123"

    def test_default_stt_model(self):
        from config import Settings
        s = Settings()
        assert s.STT_MODEL == "whisper-large-v3-turbo"

    def test_default_llm_model(self):
        from config import Settings
        s = Settings()
        assert s.LLM_MODEL == "openai/gpt-oss-120b"

    def test_default_espeak_settings(self):
        from config import Settings
        s = Settings()
        assert s.ESPEAK_EXECUTABLE == "espeak-ng"
        assert s.ESPEAK_VOICE == "en"
        assert s.ESPEAK_SPEED == 150

    def test_default_conversation_max_turns(self):
        from config import Settings
        s = Settings()
        assert s.CONVERSATION_MAX_TURNS == 10

    def test_default_groq_timeout(self):
        from config import Settings
        s = Settings()
        assert s.GROQ_TIMEOUT == 30

    def test_missing_api_key_is_empty_string(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove GROQ_API_KEY if it exists
            env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                from config import Settings
                s = Settings()
                assert s.GROQ_API_KEY == ""


# ═══════════════════════════════════════════════════════════════
#  2. MISSING API KEY HANDLING
# ═══════════════════════════════════════════════════════════════

class TestMissingAPIKey:
    """Verify components raise ValueError when API key is missing."""

    def test_stt_requires_api_key(self):
        from ai.speech_to_text import SpeechToText
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            SpeechToText(api_key="")

    def test_llm_requires_api_key(self):
        from ai.llm import LLMClient
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            LLMClient(api_key="")

    def test_tts_does_not_require_api_key(self):
        """TTS is local — no API key needed."""
        from ai.text_to_speech import TextToSpeech
        tts = TextToSpeech()  # Should not raise
        assert tts._executable == "espeak-ng"


# ═══════════════════════════════════════════════════════════════
#  3. SPEECH-TO-TEXT TESTS (MOCKED)
# ═══════════════════════════════════════════════════════════════

class TestSpeechToText:
    """Test Groq Whisper STT with mocked API calls."""

    def _make_stt(self):
        from ai.speech_to_text import SpeechToText
        stt = SpeechToText(api_key="test-key", retry_count=0)
        # Inject a mock client
        stt._client = MagicMock()
        return stt

    def test_transcribe_file_success(self):
        stt = self._make_stt()
        stt._client.audio.transcriptions.create.return_value = "Hello, how are you?"

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            result = stt.transcribe_file(path)
            assert result == "Hello, how are you?"
            stt._client.audio.transcriptions.create.assert_called_once()
        finally:
            os.unlink(path)

    def test_transcribe_file_missing_file(self):
        stt = self._make_stt()
        result = stt.transcribe_file("/nonexistent/audio.wav")
        assert result == ""
        stt._client.audio.transcriptions.create.assert_not_called()

    def test_transcribe_file_empty_file(self):
        stt = self._make_stt()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
            # File exists but is 0 bytes

        try:
            result = stt.transcribe_file(path)
            assert result == ""
        finally:
            os.unlink(path)

    def test_transcribe_file_api_error(self):
        stt = self._make_stt()
        stt._client.audio.transcriptions.create.side_effect = Exception("API timeout")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            result = stt.transcribe_file(path)
            assert result == ""
        finally:
            os.unlink(path)

    def test_transcribe_bytes_success(self):
        stt = self._make_stt()
        stt._client.audio.transcriptions.create.return_value = "What time is it?"

        result = stt.transcribe_bytes(b"\x00" * 100)
        assert result == "What time is it?"

    def test_transcribe_bytes_empty(self):
        stt = self._make_stt()
        result = stt.transcribe_bytes(b"")
        assert result == ""
        stt._client.audio.transcriptions.create.assert_not_called()

    def test_transcribe_bytes_api_error(self):
        stt = self._make_stt()
        stt._client.audio.transcriptions.create.side_effect = ConnectionError("Network down")

        result = stt.transcribe_bytes(b"\x00" * 100)
        assert result == ""

    def test_transcribe_bytes_retries_transient_failure(self):
        from ai.speech_to_text import SpeechToText

        stt = SpeechToText(
            api_key="test-key", retry_count=1, retry_delay=0
        )
        stt._client = MagicMock()
        stt._client.audio.transcriptions.create.side_effect = [
            ConnectionError("temporary network failure"),
            "Recovered transcription",
        ]

        assert stt.transcribe_bytes(b"\x00" * 100) == "Recovered transcription"
        assert stt._client.audio.transcriptions.create.call_count == 2


# ═══════════════════════════════════════════════════════════════
#  4. LLM TESTS (MOCKED)
# ═══════════════════════════════════════════════════════════════

class TestLLMClient:
    """Test Groq LLM client with mocked API calls."""

    def _make_llm(self):
        from ai.llm import LLMClient
        llm = LLMClient(api_key="test-key", retry_count=0)
        llm._client = MagicMock()
        return llm

    def _mock_response(self, llm, text):
        """Set up the mock to return a specific response."""
        mock_choice = MagicMock()
        mock_choice.message.content = text
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        llm._client.chat.completions.create.return_value = mock_completion

    def test_query_success(self):
        llm = self._make_llm()
        self._mock_response(llm, "It's 3 PM right now.")

        result = llm.query("What time is it?")
        assert result == "It's 3 PM right now."
        llm._client.chat.completions.create.assert_called_once()

    def test_query_with_history(self):
        llm = self._make_llm()
        self._mock_response(llm, "You're welcome!")

        history = [
            {"role": "user", "content": "Thanks!"},
            {"role": "assistant", "content": "Happy to help."},
        ]
        result = llm.query("Really appreciate it.", conversation_history=history)
        assert result == "You're welcome!"

        # Verify messages include system prompt + history + new message
        call_args = llm._client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert len(messages) == 4  # system + 2 history + 1 new

    def test_query_empty_message(self):
        llm = self._make_llm()
        result = llm.query("")
        assert result == ""
        llm._client.chat.completions.create.assert_not_called()

    def test_query_whitespace_only(self):
        llm = self._make_llm()
        result = llm.query("   ")
        assert result == ""

    def test_query_api_error(self):
        llm = self._make_llm()
        llm._client.chat.completions.create.side_effect = Exception("Rate limit exceeded")

        result = llm.query("Tell me a joke.")
        assert result == ""

    def test_query_retries_rate_limit(self, monkeypatch):
        from ai.llm import LLMClient

        class RateLimitError(Exception):
            status_code = 429

        monkeypatch.setattr("network.retry.time.sleep", lambda _delay: None)
        llm = LLMClient(api_key="test-key", retry_count=1, retry_delay=0)
        llm._client = MagicMock()
        completion = MagicMock()
        completion.choices[0].message.content = "Ready."
        llm._client.chat.completions.create.side_effect = [
            RateLimitError("retry later"),
            completion,
        ]

        assert llm.query("Tell me a joke.") == "Ready."
        assert llm._client.chat.completions.create.call_count == 2

    def test_default_system_prompt(self):
        from ai.llm import LLMClient
        llm = LLMClient(api_key="test-key")
        assert "VIHAAN" in llm._system_prompt

    def test_custom_system_prompt(self):
        from ai.llm import LLMClient
        llm = LLMClient(api_key="test-key", system_prompt="You are a robot.")
        assert llm._system_prompt == "You are a robot."

    def test_model_and_params(self):
        from ai.llm import LLMClient
        llm = LLMClient(
            api_key="test-key",
            model="openai/gpt-oss-120b",
            max_tokens=100,
            temperature=0.5,
        )
        assert llm._model == "openai/gpt-oss-120b"
        assert llm._max_tokens == 100
        assert llm._temperature == 0.5


# ═══════════════════════════════════════════════════════════════
#  5. CONVERSATION MANAGER TESTS
# ═══════════════════════════════════════════════════════════════

class TestConversationManager:
    """Test conversation history management."""

    def _make_convo(self, max_turns=5):
        from ai.conversation import ConversationManager
        return ConversationManager(
            system_prompt="You are VIHAAN.",
            max_turns=max_turns,
        )

    def test_initial_state(self):
        convo = self._make_convo()
        assert convo.turn_count == 0
        assert convo.system_prompt == "You are VIHAAN."

    def test_add_messages(self):
        convo = self._make_convo()
        convo.add_user_message("Hello")
        convo.add_assistant_message("Hi there!")
        assert convo.turn_count == 2

    def test_get_messages_includes_system_prompt(self):
        convo = self._make_convo()
        convo.add_user_message("Hi")
        messages = convo.get_messages()
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are VIHAAN."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hi"

    def test_get_history_excludes_system_prompt(self):
        convo = self._make_convo()
        convo.add_user_message("Hi")
        history = convo.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"

    def test_clear(self):
        convo = self._make_convo()
        convo.add_user_message("Hello")
        convo.add_assistant_message("Hi!")
        convo.clear()
        assert convo.turn_count == 0
        assert convo.get_history() == []

    def test_trimming(self):
        convo = self._make_convo(max_turns=2)
        # Add 3 full turns (6 messages) — should trim to 2 turns (4 messages)
        for i in range(3):
            convo.add_user_message(f"Q{i}")
            convo.add_assistant_message(f"A{i}")
        assert convo.turn_count == 4  # 2 turns × 2 messages
        history = convo.get_history()
        assert history[0]["content"] == "Q1"  # Q0/A0 was trimmed

    def test_system_prompt_setter(self):
        convo = self._make_convo()
        convo.system_prompt = "New prompt"
        assert convo.system_prompt == "New prompt"
        messages = convo.get_messages()
        assert messages[0]["content"] == "New prompt"


# ═══════════════════════════════════════════════════════════════
#  6. TEXT-TO-SPEECH TESTS (MOCKED SUBPROCESS)
# ═══════════════════════════════════════════════════════════════

class TestTextToSpeech:
    """Test eSpeak NG TTS with mocked subprocess calls."""

    def _make_tts(self):
        from ai.text_to_speech import TextToSpeech
        return TextToSpeech(executable="espeak-ng", voice="en", speed=150)

    def test_build_command_speak(self):
        tts = self._make_tts()
        cmd = tts.build_command("Hello world")
        assert cmd == ["espeak-ng", "-v", "en", "-s", "150", "--", "Hello world"]

    def test_build_command_with_output_file(self):
        tts = self._make_tts()
        cmd = tts.build_command("Test", output_file="out.wav")
        assert "-w" in cmd
        assert "out.wav" in cmd

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    @patch("ai.text_to_speech.subprocess.run")
    def test_speak_success(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        tts = self._make_tts()
        result = tts.speak("Hello")
        assert result is True
        mock_run.assert_called_once()

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    @patch("ai.text_to_speech.subprocess.run")
    def test_speak_subprocess_error(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=1, stderr="error msg")
        tts = self._make_tts()
        result = tts.speak("Hello")
        assert result is False

    @patch("ai.text_to_speech.shutil.which", return_value=None)
    def test_speak_espeak_missing(self, mock_which):
        from ai.text_to_speech import TextToSpeech
        # Also mock the Windows fallback path check
        with patch("ai.text_to_speech.Path.is_file", return_value=False):
            tts = TextToSpeech()
            result = tts.speak("Hello")
            assert result is False

    @patch("ai.text_to_speech.shutil.which", return_value=None)
    def test_is_available_false(self, mock_which):
        with patch("ai.text_to_speech.Path.is_file", return_value=False):
            tts = self._make_tts()
            assert tts.is_available() is False

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    def test_is_available_true(self, mock_which):
        tts = self._make_tts()
        assert tts.is_available() is True

    def test_speak_empty_text(self):
        tts = self._make_tts()
        result = tts.speak("")
        assert result is False

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    @patch("ai.text_to_speech.subprocess.run")
    def test_speak_timeout(self, mock_run, mock_which):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("espeak-ng", 30)
        tts = self._make_tts()
        result = tts.speak("Hello")
        assert result is False

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    @patch("ai.text_to_speech.subprocess.run")
    def test_save_to_file_success(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        tts = self._make_tts()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "speech.wav")
            result = tts.save_to_file("Hello", filepath)
            assert result != ""
            # Verify -w flag was used
            call_cmd = mock_run.call_args[0][0]
            assert "-w" in call_cmd


# ═══════════════════════════════════════════════════════════════
#  7. FULL PIPELINE INTEGRATION TESTS (ALL MOCKED)
# ═══════════════════════════════════════════════════════════════

class TestAIPipeline:
    """Test the AI pipeline with all components mocked."""

    def _make_pipeline(self):
        from ai.pipeline import AIPipeline
        from ai.speech_to_text import SpeechToText
        from ai.llm import LLMClient
        from ai.text_to_speech import TextToSpeech
        from ai.conversation import ConversationManager

        stt = SpeechToText(api_key="test-key")
        stt._client = MagicMock()

        llm = LLMClient(api_key="test-key")
        llm._client = MagicMock()

        tts = TextToSpeech()

        convo = ConversationManager(system_prompt="You are VIHAAN.")

        return AIPipeline(stt=stt, llm=llm, tts=tts, conversation=convo)

    def _setup_success_mocks(self, pipeline):
        """Set up mocks for a successful pipeline run."""
        pipeline.stt._client.audio.transcriptions.create.return_value = "What is Python?"

        mock_choice = MagicMock()
        mock_choice.message.content = "Python is a programming language."
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        pipeline.llm._client.chat.completions.create.return_value = mock_completion

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    @patch("ai.text_to_speech.subprocess.run")
    def test_full_pipeline_success(self, mock_run, mock_which, caplog):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        pipeline = self._make_pipeline()
        self._setup_success_mocks(pipeline)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            result = pipeline.process_audio_file(path)
            assert result.transcription == "What is Python?"
            assert result.response == "Python is a programming language."
            assert result.spoken is True
            assert result.error is None
            messages = pipeline.llm._client.chat.completions.create.call_args.kwargs[
                "messages"
            ]
            assert [message["role"] for message in messages] == ["system", "user"]
            assert messages[-1]["content"] == "What is Python?"
            assert "What is Python?" not in caplog.text
            assert "Python is a programming language." not in caplog.text
        finally:
            os.unlink(path)

    def test_pipeline_stt_failure(self):
        pipeline = self._make_pipeline()
        pipeline.stt._client.audio.transcriptions.create.side_effect = Exception("API error")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            result = pipeline.process_audio_file(path)
            assert result.transcription == ""
            assert result.error is not None
            assert "STT" in result.error
        finally:
            os.unlink(path)

    def test_pipeline_llm_failure(self):
        pipeline = self._make_pipeline()
        pipeline.stt._client.audio.transcriptions.create.return_value = "Hello"
        pipeline.llm._client.chat.completions.create.side_effect = Exception("LLM down")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            result = pipeline.process_audio_file(path)
            assert result.transcription == "Hello"
            assert result.response == ""
            assert result.error is not None
            assert "LLM" in result.error
            assert pipeline.conversation.get_history() == []
        finally:
            os.unlink(path)

    def test_pipeline_tts_failure_nonfatal(self):
        """TTS failure should NOT crash the pipeline."""
        pipeline = self._make_pipeline()
        self._setup_success_mocks(pipeline)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            # Patch TTS.is_available to return False (espeak-ng missing)
            with patch.object(pipeline.tts, "is_available", return_value=False):
                result = pipeline.process_audio_file(path)
                assert result.transcription == "What is Python?"
                assert result.response == "Python is a programming language."
                assert result.spoken is False
                assert result.error is None  # TTS fail is non-fatal
        finally:
            os.unlink(path)

    def test_pipeline_skip_tts(self):
        pipeline = self._make_pipeline()
        self._setup_success_mocks(pipeline)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            result = pipeline.process_audio_file(path, speak=False)
            assert result.transcription == "What is Python?"
            assert result.response == "Python is a programming language."
            assert result.spoken is False
        finally:
            os.unlink(path)

    def test_pipeline_updates_conversation(self):
        pipeline = self._make_pipeline()
        self._setup_success_mocks(pipeline)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"\x00" * 100)
            path = f.name

        try:
            pipeline.process_audio_file(path, speak=False)
            history = pipeline.conversation.get_history()
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "What is Python?"
            assert history[1]["role"] == "assistant"
            sent_messages = pipeline.llm._client.chat.completions.create.call_args.kwargs[
                "messages"
            ]
            assert [
                message["content"]
                for message in sent_messages
                if message["role"] == "user"
            ] == ["What is Python?"]
        finally:
            os.unlink(path)

    def test_pipeline_clear_history(self):
        pipeline = self._make_pipeline()
        pipeline.conversation.add_user_message("test")
        assert pipeline.conversation.turn_count == 1
        pipeline.clear_history()
        assert pipeline.conversation.turn_count == 0

    @patch("ai.text_to_speech.shutil.which", return_value="/usr/bin/espeak-ng")
    @patch("ai.text_to_speech.subprocess.run")
    def test_pipeline_process_bytes(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        pipeline = self._make_pipeline()
        self._setup_success_mocks(pipeline)

        result = pipeline.process_audio_bytes(b"\x00" * 100)
        assert result.transcription == "What is Python?"
        assert result.response == "Python is a programming language."
        sent_messages = pipeline.llm._client.chat.completions.create.call_args.kwargs[
            "messages"
        ]
        assert [
            message["content"]
            for message in sent_messages
            if message["role"] == "user"
        ] == ["What is Python?"]


def test_api_error_logs_do_not_include_error_message(caplog):
    from ai.llm import LLMClient

    client = LLMClient(api_key="mock-secret")
    client._client = MagicMock()
    client._client.chat.completions.create.side_effect = RuntimeError(
        "credential mock-secret must not be logged"
    )

    assert client.query("hello") == ""
    assert "mock-secret" not in caplog.text
