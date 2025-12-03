from __future__ import annotations

import abc
from typing import Protocol


class OrderExecutor(Protocol):
    async def submit(self, exchange: str, pair: str, side: str, amount: float, price: float | None):
        ...


class Strategy(abc.ABC):
    def __init__(self, name: str, executor: OrderExecutor):
        self.name = name
        self.executor = executor

    @abc.abstractmethod
    async def run_once(self) -> None:
        ...


