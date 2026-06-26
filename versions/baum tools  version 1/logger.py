from __future__ import annotations

import logging

from constants import LOG_PATH, LOGS_DIR


def configure_logging() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )
