from __future__ import annotations

import asyncio
from typing import Callable

import structlog

logger = structlog.get_logger(__name__)


class Notifier:
    def __init__(self, sink: Callable[[str], None] | None = None) -> None:
        self.sink = sink or (lambda message: logger.info("notification", message=message))
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def publish(self, message: str) -> None:
        await self._queue.put(message)

    async def run(self) -> None:
        while True:
            message = await self._queue.get()
            self.sink(message)
            self._queue.task_done()


