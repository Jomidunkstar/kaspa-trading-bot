from __future__ import annotations

from prometheus_client import Counter, Gauge, start_http_server

price_gauge = Gauge("kaspa_price", "Latest Kaspa price per exchange", labelnames=["exchange", "pair"])
balance_gauge = Gauge("exchange_balance", "Exchange balances", labelnames=["exchange", "asset"])
order_counter = Counter("orders_total", "Orders sent", labelnames=["exchange", "pair", "side"])


def start_metrics_server(host: str, port: int) -> None:
    start_http_server(port, addr=host)


def set_price(exchange: str, pair: str, price: float) -> None:
    price_gauge.labels(exchange=exchange, pair=pair).set(price)


def set_balance(exchange: str, asset: str, amount: float) -> None:
    balance_gauge.labels(exchange=exchange, asset=asset).set(amount)


def record_order(exchange: str, pair: str, side: str) -> None:
    order_counter.labels(exchange=exchange, pair=pair, side=side).inc()


