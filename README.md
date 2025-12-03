# Kaspa Trading Bot

Production-grade reference implementation for a Kaspa-focused trading stack. The bot bridges centralized exchanges (via CCXT) with native Kaspa node connectivity for balance checks, UTXO tracking, and fast settlement workflows. It targets professional operators who need modular strategies, strong observability, and infrastructure-ready deployment assets.

## Features
- Modular async Python 3.11 stack built around ccxt, Kaspa RPC, PostgreSQL, and Redis.
- Strategy runner with sample market-making and two-legged arbitrage flows.
- Unified order executor with rate limiting, audit logging, and Prometheus metrics.
- Kaspa node integration using JSON-RPC + websocket notifications (getUtxosByAddresses, getBalanceByAddress, submitTransaction).
- Dockerfile + docker-compose for reproducible dev clusters (bot, Postgres, Redis).
- Security-conscious configuration: env-driven secrets, audit trail, notification hooks, IP allowlist guidance.

## Architecture Overview
```
┌────────────┐     ┌───────────────┐     ┌──────────────┐
│ Strategies │ --> │ OrderExecutor │ --> │ Exchanges    │
└────────────┘     └───────────────┘     └──────────────┘
        │                    │                    │
        v                    v                    │
┌────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Risk Engine│<--> │ Audit & Metrics  │<--> │ Redis / DB   │
└────────────┘     └──────────────────┘     └──────────────┘
        │                                         ▲
        v                                         │
      Kaspa RPC -----------------------------------
```

### Key Modules
- `src/config.py` - Pydantic settings loader (env + JSON nested exchange creds).
- `src/exchanges/` - CCXT client wrappers and exchange manager.
- `src/kaspa/` - RPC + wallet helpers for UTXO discovery and raw tx submission.
- `src/strategies/` - Base class plus `MarketMakerStrategy` and `ArbitrageStrategy`.
- `src/workers/` - Orderbook fetch loop, strategy scheduler, shared executor.
- `src/services/` - Prometheus metrics, async notifier, append-only audit log.
- `src/risk/` - Token-bucket rate limiter and basic risk guardrails.

## Getting Started
### 1. Requirements
- Python 3.11+
- Docker Desktop (for optional compose workflow)
- Kaspa node RPC/WebSocket access (default `localhost:16110`)
- Exchange API keys with IP allowlist for the machine running the bot

### 2. Clone & Install
```bash
git clone https://github.com/your-org/kaspa-trading-bot.git
cd kaspa-trading-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` at the repo root:
```env
ENVIRONMENT=development
KASPA_RPC_URL=http://localhost:16110
KASPA_WS_URL=ws://localhost:16110/ws
KASPA_WALLET_ADDRESS=kaspatest:qp5f0example
POSTGRES_DSN=postgresql://bot:bot@localhost:5432/kaspa_bot
REDIS_URL=redis://localhost:6379/0
METRICS_HOST=0.0.0.0
METRICS_PORT=9300
EXCHANGES=[{"name":"mexc","api_key":"xxx","secret_key":"yyy"},{"name":"gateio","api_key":"aaa","secret_key":"bbb"}]
ORDERBOOK_PAIRS=["KAS/USDT","KAS/BTC"]
```
> Never commit real API keys. Back secrets with Vault/HSM in production.

### 4. Run Locally
```bash
python -m src.main
```

### 5. Docker Compose
```bash
docker compose up --build
```
Services:
- `bot` - trading process (`python -m src.main`)
- `postgres` - order/audit persistence
- `redis` - cache + stream placeholder

Prometheus metrics are exposed on `http://localhost:9300/metrics`.

## Strategy Samples
- **Market Maker**: Streams order books, calculates mid-price, quotes +/- spread basis, auto-adjusts sizes.
- **Arbitrage**: Pulls mids across two exchanges, fires dual orders when spread exceeds configurable threshold.

Add your own strategies by inheriting `Strategy` in `src/strategies/base.py` and wiring into `StrategyWorker`.

## Kaspa Node Integration
- `KaspaRpcClient` calls `getBalanceByAddress`, `getUtxosByAddresses`, `submitTransaction`.
- Websocket consumer placeholder allows subscribing to mempool notifications.
- `KaspaWallet` adapts RPC payloads into typed UTXOs to construct/sign raw transactions using your signing stack.

## Observability
- Structured JSON logging via `structlog`.
- Prometheus counters/gauges for prices, balances, order tally.
- Append-only `storage/audit.log` for compliance and post-trade review.

## Security Checklist
- Store exchange keys in Vault / AWS Secrets Manager; inject via env at runtime.
- Enforce IP allowlists on exchange dashboards.
- Use dedicated withdrawal addresses and HSM-backed Kaspa private keys.
- Respect CCXT/exchange rate limits (token bucket) and exponential backoff on `429`.
- Log every withdrawal/order to an immutable store (S3, GCS, etc.) in addition to local audit file.

## Deployment Notes
- Target low-latency regions near exchanges when market making (<100 ms signal->order).
- For arbitrage, co-locate redundant bots per venue pair; use Redis streams/Kafka for cross-service messaging.
- Scale via Kubernetes (one Deployment per strategy flavor) + GitHub Actions CI publishing images.

## Testing & Linting
```bash
ruff check src
pytest
```

## Roadmap Ideas
- Integrate native Kaspa transaction builder (rusty-kaspa bindings) for instant withdrawals.
- Plug in streaming order books via exchange websockets instead of polling.
- Add health endpoints + OpenTelemetry tracing.

## License
Apache-2.0 (or adjust to your needs). Use at your own risk; exchange trading and blockchain transactions involve capital risk.
# Kaspa Trading Bot

Production-grade reference implementation for a Kaspa-focused trading stack. The bot bridges centralized exchanges (via CCXT) with native Kaspa node connectivity for balance checks, UTXO tracking, and fast settlement workflows. It targets professional operators who need modular strategies, strong observability, and infrastructure-ready deployment assets.

## Features
- Modular async Python 3.11 stack built around ccxt, Kaspa RPC, PostgreSQL, and Redis.
- Strategy runner with sample market-making and two-legged arbitrage flows.
- Unified order executor with rate limiting, audit logging, and Prometheus metrics.
- Kaspa node integration using JSON-RPC + websocket notifications (getUtxosByAddresses, getBalanceByAddress, submitTransaction).
- Dockerfile + docker-compose for reproducible dev clusters (bot, Postgres, Redis).
- Security-conscious configuration: env-driven secrets, audit trail, notification hooks, IP allowlist guidance.

## Architecture Overview
```
          
 Strategies  -->  OrderExecutor  -->  Exchanges    
          
                                                
        v                    v                    
          
 Risk Engine<-->  Audit & Metrics  <-->  Redis / DB   
          
                                                 
        v                                         
      Kaspa RPC -----------------------------------
```

### Key Modules
- `src/config.py` - Pydantic settings loader (env + JSON nested exchange creds).
- `src/exchanges/` - CCXT client wrappers and exchange manager.
- `src/kaspa/` - RPC + wallet helpers for UTXO discovery and raw tx submission.
- `src/strategies/` - Base class plus `MarketMakerStrategy` and `ArbitrageStrategy`.
- `src/workers/` - Orderbook fetch loop, strategy scheduler, shared executor.
- `src/services/` - Prometheus metrics, async notifier, append-only audit log.
- `src/risk/` - Token-bucket rate limiter and basic risk guardrails.

## Getting Started
### 1. Requirements
- Python 3.11+
- Docker Desktop (for optional compose workflow)
- Kaspa node RPC/WebSocket access (default `localhost:16110`)
- Exchange API keys with IP allowlist for the machine running the bot

### 2. Clone & Install
```bash
git clone https://github.com/your-org/kaspa-trading-bot.git
cd kaspa-trading-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` at the repo root:
```env
ENVIRONMENT=development
KASPA_RPC_URL=http://localhost:16110
KASPA_WS_URL=ws://localhost:16110/ws
KASPA_WALLET_ADDRESS=kaspatest:qp5f0example
POSTGRES_DSN=postgresql://bot:bot@localhost:5432/kaspa_bot
REDIS_URL=redis://localhost:6379/0
METRICS_HOST=0.0.0.0
METRICS_PORT=9300
EXCHANGES=[{"name":"mexc","api_key":"xxx","secret_key":"yyy"},{"name":"gateio","api_key":"aaa","secret_key":"bbb"}]
ORDERBOOK_PAIRS=["KAS/USDT","KAS/BTC"]
```
> Never commit real API keys. Back secrets with Vault/HSM in production.

### 4. Run Locally
```bash
python -m src.main
```

### 5. Docker Compose
```bash
docker compose up --build
```
Services:
- `bot` - trading process (`python -m src.main`)
- `postgres` - order/audit persistence
- `redis` - cache + stream placeholder

Prometheus metrics are exposed on `http://localhost:9300/metrics`.

## Strategy Samples
- **Market Maker**: Streams order books, calculates mid-price, quotes +/- spread basis, auto-adjusts sizes.
- **Arbitrage**: Pulls mids across two exchanges, fires dual orders when spread exceeds configurable threshold.

Add your own strategies by inheriting `Strategy` in `src/strategies/base.py` and wiring into `StrategyWorker`.

## Kaspa Node Integration
- `KaspaRpcClient` calls `getBalanceByAddress`, `getUtxosByAddresses`, `submitTransaction`.
- Websocket consumer placeholder allows subscribing to mempool notifications.
- `KaspaWallet` adapts RPC payloads into typed UTXOs to construct/sign raw transactions using your signing stack.

## Observability
- Structured JSON logging via `structlog`.
- Prometheus counters/gauges for prices, balances, order tally.
- Append-only `storage/audit.log` for compliance and post-trade review.

## Security Checklist
- Store exchange keys in Vault / AWS Secrets Manager; inject via env at runtime.
- Enforce IP allowlists on exchange dashboards.
- Use dedicated withdrawal addresses and HSM-backed Kaspa private keys.
- Respect CCXT/exchange rate limits (token bucket) and exponential backoff on `429`.
- Log every withdrawal/order to an immutable store (S3, GCS, etc.) in addition to local audit file.

## Deployment Notes
- Target low-latency regions near exchanges when market making (<100 ms signal->order).
- For arbitrage, co-locate redundant bots per venue pair; use Redis streams/Kafka for cross-service messaging.
- Scale via Kubernetes (one Deployment per strategy flavor) + GitHub Actions CI publishing images.

## Testing & Linting
```bash
ruff check src
pytest
```

## Roadmap Ideas
- Integrate native Kaspa transaction builder (rusty-kaspa bindings) for instant withdrawals.
- Plug in streaming order books via exchange websockets instead of polling.
- Add health endpoints + OpenTelemetry tracing.

## License
Apache-2.0 (or adjust to your needs). Use at your own risk; exchange trading and blockchain transactions involve capital risk.

