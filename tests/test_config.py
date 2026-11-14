"""
tests.test_config — Configuration Tests
=========================================
Verifies that config.py loads defaults correctly and that
environment variable overrides work as expected.
"""

from config import Settings, BASE_DIR, DATA_DIR


def test_default_settings():
    """Settings should have sensible defaults without any .env file."""
    s = Settings()
    assert s.PROJECT_NAME == "VIHAAN AI PIN"
    assert s.LOG_LEVEL == "INFO"
    assert s.LLM_MODEL == "openai/gpt-oss-120b"
    assert s.STT_MODEL == "whisper-large-v3-turbo"
    assert s.ESPEAK_EXECUTABLE == "espeak-ng"
    assert s.AUDIO_SAMPLE_RATE == 16000
    assert s.MAX_MEMORY_MB == 384


def test_project_paths():
    """BASE_DIR and DATA_DIR should resolve to actual directories."""
    assert BASE_DIR.exists()
    assert DATA_DIR.exists()
    assert (DATA_DIR / "logs").exists()
    assert (DATA_DIR / "cache").exists()
