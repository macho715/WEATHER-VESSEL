"""로깅 설정 유틸리티. | Logging configuration utility."""

from __future__ import annotations

import logging
import os
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    """구조화 로깅 설정. | Configure structured logging."""

    env_level = os.getenv("WV_LOG_LEVEL", "INFO")
    effective_level = level if level is not None else env_level
    log_level = effective_level.upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
