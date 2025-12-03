from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class ExchangeKeys(BaseSettings):
    name: str
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None
    subaccount: Optional[str] = None


class Settings(BaseSettings):
    environment: str = Field("development", description="deployment environment name")
    exchanges: List[ExchangeKeys] = Field(default_factory=list)
    kaspa_rpc_url: str = Field("http://localhost:16110", description="Kaspa node RPC URL")
    kaspa_ws_url: str = Field("ws://localhost:16110/ws", description="Kaspa node websocket URL")
    kaspa_wallet_address: str = Field(..., description="Primary Kaspa wallet address")
    postgres_dsn: str = Field("postgresql://bot:bot@localhost:5432/kaspa_bot", description="Postgres DSN")
    redis_url: str = Field("redis://localhost:6379/0", description="Redis connection string")
    metrics_host: str = "0.0.0.0"
    metrics_port: int = 9300
    log_level: str = "INFO"
    rate_limit_per_sec: int = Field(20, ge=1)
    strategy_refresh_sec: int = Field(2, ge=1)
    orderbook_pairs: List[str] = Field(default_factory=lambda: ["KAS/USDT", "KAS/BTC"])
    audit_log_path: Path = Path("storage/audit.log")

    @validator("exchanges", pre=True)
    def _coerce_exchange_list(cls, value):
        if isinstance(value, str):
            import json

            return json.loads(value)
        return value

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache
def get_settings() -> Settings:
    return Settings()


