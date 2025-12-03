from __future__ import annotations

import asyncio
from typing import List

import structlog

from src.config import get_settings
from src.strategies.base import Strategy

logger = structlog.get_logger(__name__)


class StrategyWorker:
    def __init__(self, strategies: List[Strategy]) -> None:
        self.strategies = strategies
        self.settings = get_settings()

    async def run(self) -> None:
        while True:
            for strategy in self.strategies:
                try:
                    await strategy.run_once()
                except Exception as exc:  # pragma: no cover
                    logger.exception("strategy_error", strategy=strategy.name, error=str(exc))
            await asyncio.sleep(self.settings.strategy_refresh_sec)


