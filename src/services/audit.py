from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


class AuditLog:
    def __init__(self, file_path: Path | None = None) -> None:
        settings = get_settings()
        self.path = file_path or settings.audit_log_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def write(self, event: dict) -> None:
        import json

        payload = json.dumps(event)
        await self._queue.put(payload)

    async def run(self) -> None:
        while True:
            payload = await self._queue.get()
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(payload + "\n")
            self._queue.task_done()
            logger.debug("audit_event_written")


