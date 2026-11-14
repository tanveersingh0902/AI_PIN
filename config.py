"""
Configuration — config.py
=========================
Central configuration loaded from environment variables and .env file.
Uses a lightweight dataclass so we avoid heavy frameworks on the Pi.

Priority: ENV vars  >  .env file  >  defaults defined here.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

# ── Load .env if python-dotenv is available ────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; we fall back to OS env vars


def _env(key: str, default: str = "") -> str:
    """Read an environment variable with a fallback default."""
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("1", "true", "yes")


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


# ── Project paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"
MODEL_DIR = DATA_DIR / "models"


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    # ── General ────────────────────────────────────────────────
    PROJECT_NAME: str = "VIHAAN AI PIN"
    VERSION: str = "0.2.0"
    DEBUG: bool = _env_bool("DEBUG", False)
    LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")

    # ── Groq API (shared key for STT + LLM) ───────────────────
    GROQ_API_KEY: str = _env("GROQ_API_KEY")

    # ── Speech-to-Text (Groq Whisper) ─────────────────────────
    STT_MODEL: str = _env("STT_MODEL", "whisper-large-v3-turbo")

    # ── LLM (Groq) ────────────────────────────────────────────
    LLM_MODEL: str = _env("LLM_MODEL", "openai/gpt-oss-120b")
    LLM_MAX_TOKENS: int = _env_int("LLM_MAX_TOKENS", 256)
    LLM_TEMPERATURE: float = float(_env("LLM_TEMPERATURE", "0.7"))
    LLM_SYSTEM_PROMPT: str = _env(
        "LLM_SYSTEM_PROMPT",
        "You are VIHAAN, a helpful and concise voice assistant running on "
        "a wearable AI pin. Keep responses short (1–3 sentences) and "
        "spoken-language friendly. Avoid markdown, code blocks, or long "
        "lists. Be warm, direct, and useful."
    )

    # ── Text-to-Speech (eSpeak NG — local executable) ─────────
    ESPEAK_EXECUTABLE: str = _env("ESPEAK_EXECUTABLE", "espeak-ng")
    ESPEAK_VOICE: str = _env("ESPEAK_VOICE", "en")
    ESPEAK_SPEED: int = _env_int("ESPEAK_SPEED", 150)

    # ── Conversation ──────────────────────────────────────────
    CONVERSATION_MAX_TURNS: int = _env_int("CONVERSATION_MAX_TURNS", 10)

    # ── Groq API settings ─────────────────────────────────────
    GROQ_TIMEOUT: int = _env_int("GROQ_TIMEOUT", 30)

    # ── Wake Word ─────────────────────────────────────────────
    WAKE_WORD: str = _env("WAKE_WORD", "hey vihaan")

    # ── Audio ─────────────────────────────────────────────────
    AUDIO_SAMPLE_RATE: int = _env_int("AUDIO_SAMPLE_RATE", 16000)
    AUDIO_CHANNELS: int = _env_int("AUDIO_CHANNELS", 1)
    AUDIO_CHUNK_SIZE: int = _env_int("AUDIO_CHUNK_SIZE", 1024)

    # ── Network ───────────────────────────────────────────────
    WIFI_SSID: str = _env("WIFI_SSID")
    WIFI_PASSWORD: str = _env("WIFI_PASSWORD")
    API_TIMEOUT: int = _env_int("API_TIMEOUT", 10)

    # ── Hardware (Pi-specific) ────────────────────────────────
    BUTTON_GPIO_PIN: int = _env_int("BUTTON_GPIO_PIN", 17)
    LED_GPIO_PIN: int = _env_int("LED_GPIO_PIN", 27)
    BATTERY_ADC_CHANNEL: int = _env_int("BATTERY_ADC_CHANNEL", 0)

    # ── Resource Limits (for 512 MB Pi Zero W) ────────────────
    MAX_MEMORY_MB: int = _env_int("MAX_MEMORY_MB", 384)
    CACHE_MAX_ITEMS: int = _env_int("CACHE_MAX_ITEMS", 50)


# ── Singleton instance ────────────────────────────────────────
settings = Settings()
