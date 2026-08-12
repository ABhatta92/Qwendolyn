from __future__ import annotations

import logging
from pathlib import Path

from qwendolyn import config


def get_logger(
    name: str,
    log_file: str | None = None,
) -> logging.Logger:

    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # -------------------------------------------------------------------------
    # Avoid adding duplicate handlers when the logger is requested repeatedly.
    # -------------------------------------------------------------------------

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # -------------------------------------------------------------------------
    # Console
    # -------------------------------------------------------------------------

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    # -------------------------------------------------------------------------
    # File
    # -------------------------------------------------------------------------

    if log_file:

        log_directory = Path(
            config.LOGS
        ).resolve()

        log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not log_file.endswith(
            ".log"
        ):

            log_file = (
                f"{log_file}.log"
            )

        file_handler = logging.FileHandler(
            log_directory / log_file,
            encoding="utf-8",
        )

        file_handler.setFormatter(
            formatter
        )

        logger.addHandler(
            file_handler
        )

    return logger