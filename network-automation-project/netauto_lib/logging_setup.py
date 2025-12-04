"""Global logging configuration for NetAuto.

Creates ``<logs_dir>/<log_name>`` with rotation, mirrors logs to console, and
ensures configuration is only applied once per process.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(logs_dir: str = "logs", log_name: str = "netauto.log") -> None:
    """Configure logging outputs for the CLI tool."""
    log_path = Path(logs_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / log_name

    logger = logging.getLogger()
    if _already_configured(logger, log_file):
        return

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.propagate = False
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.info("Logging initialized at %s", level_name)


def _already_configured(logger: logging.Logger, log_file: Path) -> bool:
    """Return True if handlers for the target log file already exist (internal)."""
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(log_file):
            return True
    return False
