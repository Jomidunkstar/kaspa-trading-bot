from __future__ import annotations

import asyncio
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


class RedisCache:
    def __init__(self, url: str | None = None) -> None:
        self._url = url or get_settings().redis_url
        self._client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> redis.Redis:
        async with self._lock:
            if not self._client:
                self._client = redis.from_url(self._url, decode_responses=True)
                logger.info("redis_connected", url=self._url)
        return self._client

    async def get_json(self, key: str) -> Any:
        client = await self.connect()
        raw = await client.get(key)
        if raw:
            import json

            return json.loads(raw)
        return None

    async def set_json(self, key: str, value: Any, ttl: int = 60) -> None:
        client = await self.connect()
        import json

        await client.set(key, json.dumps(value), ex=ttl)


