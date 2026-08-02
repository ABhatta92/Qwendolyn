import logging

from qwendolyn import config


def _default_log_file(name: str) -> str:
    normalized = name.lower().replace("-", "_").replace(" ", "_")

    if normalized in {"__main__", "app", "streamlit", "qwendolyn.app"}:
        return "app"

    if "llm" in normalized:
        return "llm"

    if "tool" in normalized:
        return "tools"

    if "." in normalized:
        parts = [part for part in normalized.split(".") if part and part != "qwendolyn"]
        if parts:
            return parts[-1]

    return normalized or "qwendolyn"


def get_logger(name: str, log_file: str | None = None):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    target_log_file = log_file or _default_log_file(name)
    file_handler = logging.FileHandler(config.LOGS / f"{target_log_file}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger