"""
Seed Logging System.

Provides centralized logging configuration
for the entire Seed application.
"""

from __future__ import annotations

import logging
import sys

from typing import Final


# ==================================================
# Constants
# ==================================================

LOG_FORMAT: Final[str] = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


DEFAULT_LOG_LEVEL: Final[int] = logging.INFO


# ==================================================
# Logger Configuration
# ==================================================


def setup_logger(
    name: str = "seed",
    level: int = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Create and configure a Seed logger.

    Args:
        name:
            Logger name.

        level:
            Logging level.

    Returns:
        Configured logger instance.
    """

    logger = logging.getLogger(name)

    logger.setLevel(level)


    # Prevent duplicate handlers
    if logger.handlers:
        return logger


    formatter = logging.Formatter(
        LOG_FORMAT
    )


    console_handler = logging.StreamHandler(
        sys.stdout
    )

    console_handler.setFormatter(
        formatter
    )


    logger.addHandler(
        console_handler
    )


    return logger


# ==================================================
# Default Logger
# ==================================================

logger = setup_logger()