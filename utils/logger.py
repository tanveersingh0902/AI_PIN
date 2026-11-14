"""
utils.logger — Logging Setup
==============================
Configures Python's built-in logging for the entire application.

Features:
  - Console handler with colour-friendly formatting
  - Optional rotating file handler (capped size for Pi's SD card)
  - Single call in main.py sets everything up
"""

import logging
import sys
from pathlib import Path

# Default log file location
_LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs"


def setup_logging(level: str = "INFO", log_file: str = "vihaan.log") -> None:
    """
    Configure root logger with console + optional file output.

    Parameters
    ----------
    level : str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    log_file : str
        Name of the log file inside data/logs/.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # ── Formatter ──────────────────────────────────────────────
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    datefmt = "%H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # ── Console Handler ────────────────────────────────────────
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)

    # ── File Handler (optional, safe if dir missing) ───────────
    handlers = [console]
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            _LOG_DIR / log_file,
            maxBytes=2 * 1024 * 1024,   # 2 MB cap (SD card friendly)
            backupCount=2,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except (OSError, ValueError) as error:
        logging.getLogger(__name__).warning(
            "File logging unavailable; using console output: %s", error
        )

    # ── Root Logger ────────────────────────────────────────────
    logging.basicConfig(level=log_level, handlers=handlers, force=True)
