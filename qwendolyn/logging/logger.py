from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from qwendolyn import config

DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOGGERS: dict[str, logging.Logger] = {}


def get_logger(
    name: str,
    *,
    log_file: str = "app",
    level: int = logging.INFO,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:

    key = f"{name}:{log_file}"

    if key in _LOGGERS:
        return _LOGGERS[key]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt=DEFAULT_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    if file:

        config.LOGS.mkdir(
            parents=True,
            exist_ok=True,
        )

        handler = RotatingFileHandler(
            filename=Path(config.LOGS) / f"{log_file}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if console:

        handler = logging.StreamHandler()

        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _LOGGERS[key] = logger

    return logger