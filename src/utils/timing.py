from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

import structlog

logger = structlog.get_logger(__name__)


@contextmanager
def latency_timer(metric_name: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug("latency_sample", metric=metric_name, elapsed_ms=elapsed_ms)


