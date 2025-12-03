from __future__ import annotations

import asyncio
import signal

import structlog
from dotenv import load_dotenv

from src.config import Settings, get_settings
from src.db.postgres import Postgres
from src.db.redis_cache import RedisCache
from src.exchanges.exchange_manager import ExchangeManager
from src.kaspa.wallet import KaspaWallet
from src.logging_config import configure_logging
from src.risk.risk_engine import RiskEngine, RiskLimits
from src.services import metrics
from src.services.audit import AuditLog
from src.services.notifier import Notifier
from src.strategies.arbitrage import ArbitrageConfig, ArbitrageStrategy
from src.strategies.market_maker import MarketMakerConfig, MarketMakerStrategy
from src.workers.order_executor import OrderExecutor
from src.workers.orderbook_worker import OrderbookWorker
from src.workers.strategy_worker import StrategyWorker

logger = structlog.get_logger(__name__)


async def bootstrap(settings: Settings):
    load_dotenv()
    configure_logging(settings.log_level)
    metrics.start_metrics_server(settings.metrics_host, settings.metrics_port)

    postgres = Postgres(settings.postgres_dsn)
    redis_cache = RedisCache(settings.redis_url)
    exchange_manager = ExchangeManager()
    audit_log = AuditLog(settings.audit_log_path)
    risk_engine = RiskEngine(
        RiskLimits(max_notional=50_000, max_position_pct=0.2, max_orders_per_min=60)
    )
    executor = OrderExecutor(exchange_manager, risk_engine, audit_log)
    notifier = Notifier()
    kaspa_wallet = KaspaWallet()

    exchanges = exchange_manager.list_exchanges()
    if len(exchanges) < 1:
        raise RuntimeError("Configure at least one exchange via EXCHANGES env")
    primary_exchange = exchanges[0]
    secondary_exchange = exchanges[-1]

    market_maker = MarketMakerStrategy(
        executor,
        MarketMakerConfig(pair=settings.orderbook_pairs[0], exchange=primary_exchange),
    )
    arbitrage = ArbitrageStrategy(
        executor,
        ArbitrageConfig(
            pair=settings.orderbook_pairs[0],
            exchange_a=primary_exchange,
            exchange_b=secondary_exchange,
        ),
    )
    strategy_worker = StrategyWorker([market_maker, arbitrage])
    orderbook_worker = OrderbookWorker(exchange_manager, executor)

    await postgres.connect()
    await redis_cache.connect()

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _handle_signal():
        logger.info("shutdown_signal")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    await asyncio.gather(
        audit_log.run(),
        notifier.run(),
        strategy_worker.run(),
        orderbook_worker.run(),
    )


def main():
    settings = get_settings()
    asyncio.run(bootstrap(settings))


if __name__ == "__main__":
    main()


