from __future__ import annotations

from dataclasses import dataclass

import structlog

from src.services import metrics
from src.strategies.base import Strategy

logger = structlog.get_logger(__name__)


@dataclass
class MarketMakerConfig:
    pair: str
    spread_bps: float = 8.0
    order_size: float = 200.0
    exchange: str = "mexc"


class MarketMakerStrategy(Strategy):
    def __init__(self, executor, config: MarketMakerConfig):
        super().__init__("market_maker", executor)
        self.config = config

    async def run_once(self) -> None:
        mid_price = await self.executor.mid_price(self.config.exchange, self.config.pair)
        if not mid_price:
            logger.warning("mm_no_price", pair=self.config.pair)
            return
        spread = mid_price * (self.config.spread_bps / 10000)
        bid = mid_price - spread
        ask = mid_price + spread
        size = self.config.order_size
        logger.info("mm_quotes", bid=bid, ask=ask, size=size)
        await self.executor.submit(self.config.exchange, self.config.pair, "buy", size, bid)
        await self.executor.submit(self.config.exchange, self.config.pair, "sell", size, ask)
        metrics.record_order(self.config.exchange, self.config.pair, "buy")
        metrics.record_order(self.config.exchange, self.config.pair, "sell")


