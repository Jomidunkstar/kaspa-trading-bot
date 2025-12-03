from __future__ import annotations

from dataclasses import dataclass

import structlog

from src.services import metrics
from src.strategies.base import Strategy

logger = structlog.get_logger(__name__)


@dataclass
class ArbitrageConfig:
    pair: str
    exchange_a: str
    exchange_b: str
    min_spread_pct: float = 0.6
    order_size: float = 150.0


class ArbitrageStrategy(Strategy):
    def __init__(self, executor, config: ArbitrageConfig):
        super().__init__("arbitrage", executor)
        self.config = config

    async def run_once(self) -> None:
        price_a = await self.executor.mid_price(self.config.exchange_a, self.config.pair)
        price_b = await self.executor.mid_price(self.config.exchange_b, self.config.pair)
        if not price_a or not price_b:
            return
        spread_pct = (price_b - price_a) / price_a * 100
        if abs(spread_pct) < self.config.min_spread_pct:
            logger.debug("arb_spread_insufficient", spread=spread_pct)
            return
        if spread_pct > 0:
            buy_ex, sell_ex = self.config.exchange_a, self.config.exchange_b
        else:
            buy_ex, sell_ex = self.config.exchange_b, self.config.exchange_a
        await self.executor.submit(buy_ex, self.config.pair, "buy", self.config.order_size, price_a)
        await self.executor.submit(
            sell_ex, self.config.pair, "sell", self.config.order_size, price_b
        )
        metrics.record_order(buy_ex, self.config.pair, "buy")
        metrics.record_order(sell_ex, self.config.pair, "sell")
        logger.info("arb_trade", spread_pct=spread_pct, buy=buy_ex, sell=sell_ex)


