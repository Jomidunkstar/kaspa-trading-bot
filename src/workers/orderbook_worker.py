from __future__ import annotations

import asyncio

import structlog

from src.config import get_settings
from src.exchanges.exchange_manager import ExchangeManager
from src.services import metrics
from src.workers.order_executor import OrderExecutor

logger = structlog.get_logger(__name__)


class OrderbookWorker:
    def __init__(self, exchanges: ExchangeManager, executor: OrderExecutor) -> None:
        self.exchanges = exchanges
        self.executor = executor
        self.settings = get_settings()

    async def run(self) -> None:
        while True:
            for exchange_name in self.exchanges.list_exchanges():
                client = self.exchanges.get(exchange_name)
                for pair in self.settings.orderbook_pairs:
                    try:
                        book = await client.fetch_order_book(pair)
                        bid = book["bids"][0][0]
                        ask = book["asks"][0][0]
                        mid = (bid + ask) / 2
                        self.executor.update_mid(exchange_name, pair, mid)
                        metrics.set_price(exchange_name, pair, mid)
                    except Exception as exc:  # pragma: no cover
                        logger.warning("orderbook_fetch_failed", exchange=exchange_name, pair=pair, error=str(exc))
                await asyncio.sleep(0)
            await asyncio.sleep(self.settings.strategy_refresh_sec)


