from __future__ import annotations

import ccxt.async_support as ccxt
import structlog

from src.config import ExchangeKeys
from src.risk.rate_limiter import WeightAwareLimiter

logger = structlog.get_logger(__name__)


class CCXTClient:
    def __init__(self, keys: ExchangeKeys, limiter: WeightAwareLimiter | None = None) -> None:
        self.keys = keys
        self.limiter = limiter or WeightAwareLimiter(rate=20)
        exchange_class = getattr(ccxt, keys.name)
        self.client = exchange_class(
            {
                "apiKey": keys.api_key,
                "secret": keys.secret_key,
                "password": keys.passphrase,
                "enableRateLimit": False,
            }
        )
        if keys.subaccount:
            self.client.headers = self.client.headers or {}
            self.client.headers["FTX-SUBACCOUNT"] = keys.subaccount

    async def fetch_order_book(self, symbol: str, limit: int = 50):
        async with self.limiter():
            book = await self.client.fetch_order_book(symbol, limit)
            logger.debug("orderbook_snapshot", exchange=self.keys.name, symbol=symbol)
            return book

    async def fetch_balance(self):
        async with self.limiter():
            return await self.client.fetch_balance()

    async def create_order(
        self, symbol: str, side: str, order_type: str, amount: float, price: float | None = None
    ):
        async with self.limiter():
            return await self.client.create_order(symbol, order_type, side, amount, price, params={})

    async def close(self) -> None:
        await self.client.close()


