from __future__ import annotations

from typing import Dict

import structlog

from src.exchanges.exchange_manager import ExchangeManager
from src.risk.risk_engine import RiskEngine
from src.services.audit import AuditLog

logger = structlog.get_logger(__name__)


class OrderExecutor:
    def __init__(
        self, exchanges: ExchangeManager, risk_engine: RiskEngine, audit_log: AuditLog
    ) -> None:
        self.exchanges = exchanges
        self.risk = risk_engine
        self.audit = audit_log
        self.orderbooks: Dict[str, Dict[str, float]] = {}

    def update_mid(self, exchange: str, pair: str, mid: float) -> None:
        key = f"{exchange}:{pair}"
        self.orderbooks[key] = {"mid": mid}

    async def mid_price(self, exchange: str, pair: str) -> float | None:
        key = f"{exchange}:{pair}"
        if key in self.orderbooks:
            return self.orderbooks[key]["mid"]
        client = self.exchanges.get(exchange)
        book = await client.fetch_order_book(pair)
        mid = (book["bids"][0][0] + book["asks"][0][0]) / 2
        self.orderbooks[key] = {"mid": mid}
        return mid

    async def submit(self, exchange: str, pair: str, side: str, amount: float, price: float | None):
        notional = amount * (price or await self.mid_price(exchange, pair))
        if not self.risk.can_send_order(notional, position_pct=0.05):
            return None
        client = self.exchanges.get(exchange)
        order = await client.create_order(pair, side, "limit", amount, price)
        await self.audit.write(
            {
                "exchange": exchange,
                "pair": pair,
                "side": side,
                "amount": amount,
                "price": price,
                "order_id": order.get("id"),
            }
        )
        logger.info("order_submitted", exchange=exchange, pair=pair, side=side, order_id=order.get("id"))
        return order


