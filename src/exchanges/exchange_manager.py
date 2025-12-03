from __future__ import annotations

from typing import Dict, List

import structlog

from src.config import ExchangeKeys, get_settings
from src.exchanges.ccxt_client import CCXTClient
from src.risk.rate_limiter import WeightAwareLimiter

logger = structlog.get_logger(__name__)


class ExchangeManager:
    def __init__(self) -> None:
        settings = get_settings()
        self.clients: Dict[str, CCXTClient] = {
            keys.name: CCXTClient(keys, WeightAwareLimiter(rate=settings.rate_limit_per_sec))
            for keys in settings.exchanges
        }

    def list_exchanges(self) -> List[str]:
        return list(self.clients.keys())

    def get(self, name: str) -> CCXTClient:
        try:
            return self.clients[name]
        except KeyError as exc:
            raise ValueError(f"Exchange {name} is not configured") from exc

    async def close(self) -> None:
        for client in self.clients.values():
            await client.close()


