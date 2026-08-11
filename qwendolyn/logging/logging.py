from __future__ import annotations

import logging
from pathlib import Path


LOG_DIR = Path("logs")


def get_logger(
    name: str,
    log_file: str | None = None,
) -> logging.Logger:

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    if log_file:

        LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not log_file.endswith(".log"):
            log_file = f"{log_file}.log"

        file_handler = logging.FileHandler(
            LOG_DIR / log_file,
            encoding="utf-8",
        )

        file_handler.setFormatter(
            formatter
        )

        logger.addHandler(
            file_handler
        )

    return logger