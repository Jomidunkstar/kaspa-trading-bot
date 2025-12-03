from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RiskLimits:
    max_notional: float
    max_position_pct: float
    max_orders_per_min: int


class RiskEngine:
    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits
        self._orders_this_minute = 0

    def can_send_order(self, notional: float, position_pct: float) -> bool:
        if notional > self.limits.max_notional:
            logger.warning("risk_notional_block", requested=notional, limit=self.limits.max_notional)
            return False
        if position_pct > self.limits.max_position_pct:
            logger.warning(
                "risk_position_block", requested=position_pct, limit=self.limits.max_position_pct
            )
            return False
        if self._orders_this_minute >= self.limits.max_orders_per_min:
            logger.warning("risk_order_block", count=self._orders_this_minute)
            return False
        self._orders_this_minute += 1
        return True

    def reset_counters(self) -> None:
        self._orders_this_minute = 0

    def snapshot(self) -> Dict[str, float]:
        return {
            "orders_this_minute": self._orders_this_minute,
            "max_notional": self.limits.max_notional,
            "max_position_pct": self.limits.max_position_pct,
        }


