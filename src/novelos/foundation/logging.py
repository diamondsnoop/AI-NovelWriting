import logging
from typing import Any


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_llm_call(logger: logging.Logger, payload: dict[str, Any]) -> None:
    logger.info("llm_call %s", payload)
