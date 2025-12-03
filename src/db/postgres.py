from __future__ import annotations

import asyncpg
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


class Postgres:
    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or get_settings().postgres_dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self._pool:
            return
        self._pool = await asyncpg.create_pool(self._dsn, statement_cache_size=0)
        logger.info("postgres_connected", dsn=self._dsn)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            logger.info("postgres_closed")

    async def fetch(self, sql: str, *args):
        if not self._pool:
            raise RuntimeError("Postgres pool not initialized")
        async with self._pool.acquire() as conn:
            return await conn.fetch(sql, *args)

    async def execute(self, sql: str, *args):
        if not self._pool:
            raise RuntimeError("Postgres pool not initialized")
        async with self._pool.acquire() as conn:
            return await conn.execute(sql, *args)


