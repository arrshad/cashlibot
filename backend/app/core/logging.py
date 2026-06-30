"""Structured logging setup for both bot and api processes."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str) -> None:
    """Configure root logger with a single stderr handler."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()

    # Reset any handlers already set by libraries.
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s — %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(log_level)

    # aiogram + sqlalchemy are chatty at INFO. Keep them at WARNING by default.
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
