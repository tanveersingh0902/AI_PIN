"""
VIHAAN AI PIN — Main Entry Point
=================================
Wearable AI Voice Assistant based on Raspberry Pi Zero W.

This is the top-level launcher. It:
  1. Loads configuration and environment variables.
  2. Detects the runtime platform (Windows dev ↔ Raspberry Pi).
  3. Initialises the appropriate hardware layer (real or simulated).
  4. Starts the voice-assistant pipeline loop.

Usage
-----
  Development (Windows):   python main.py
  Production  (Pi):        python3 main.py
"""

import sys
import signal
import logging

from config import settings
from utils.logger import setup_logging
from utils.platform_detect import detect_platform, Platform
from backend.pipeline import VoiceAssistantPipeline


def graceful_shutdown(signum, frame):
    """Handle SIGINT / SIGTERM for clean exit."""
    logging.info("Shutdown signal received — cleaning up …")
    sys.exit(0)


def main():
    # ── 1. Logging ──────────────────────────────────────────────
    setup_logging(level=settings.LOG_LEVEL)
    logger = logging.getLogger("vihaan")

    # ── 2. Platform Detection ──────────────────────────────────
    platform = detect_platform()
    logger.info(f"Platform detected: {platform.value}")
    logger.info(f"Project : {settings.PROJECT_NAME} v{settings.VERSION}")

    if platform == Platform.RASPBERRY_PI:
        logger.info("Running on Raspberry Pi — using real hardware drivers.")
    else:
        logger.info("Running on development machine — using simulated hardware.")

    # ── 3. Signal Handlers ─────────────────────────────────────
    signal.signal(signal.SIGINT, graceful_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, graceful_shutdown)

    # ── 4. Pipeline ────────────────────────────────────────────
    pipeline = VoiceAssistantPipeline(platform=platform)
    logger.info("Voice assistant pipeline initialised.")

    try:
        pipeline.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        pipeline.shutdown()
        logger.info("VIHAAN AI PIN shut down cleanly.")


if __name__ == "__main__":
    main()
