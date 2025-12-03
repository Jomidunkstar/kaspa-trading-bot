from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable, TypeVar

T = TypeVar("T")


async def gather_limited(*coroutines: Awaitable[T], limit: int = 10) -> list[T]:
    semaphore = asyncio.Semaphore(limit)

    async def _run(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_run(c) for c in coroutines))


@asynccontextmanager
async def lifespan(task_factory: Callable[[], Awaitable[None]]) -> AsyncIterator[None]:
    task = asyncio.create_task(task_factory())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


