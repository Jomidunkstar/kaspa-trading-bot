from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx
import structlog
import websockets

from src.config import get_settings

logger = structlog.get_logger(__name__)


class KaspaRpcClient:
    def __init__(self, rpc_url: str | None = None, ws_url: str | None = None) -> None:
        settings = get_settings()
        self.rpc_url = rpc_url or settings.kaspa_rpc_url
        self.ws_url = ws_url or settings.kaspa_ws_url
        self._http = httpx.AsyncClient(timeout=10)
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._lock = asyncio.Lock()

    async def call(self, method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
        response = await self._http.post(self.rpc_url, json=payload)
        response.raise_for_status()
        data = response.json()
        if "error" in data and data["error"]:
            raise RuntimeError(data["error"])
        return data["result"]

    async def get_balance(self, address: str) -> Dict[str, Any]:
        return await self.call("getBalanceByAddress", {"address": address})

    async def get_utxos(self, addresses: list[str]) -> Dict[str, Any]:
        return await self.call("getUtxosByAddresses", {"addresses": addresses})

    async def submit_transaction(self, raw_tx: str) -> str:
        result = await self.call("submitTransaction", {"transaction": raw_tx})
        return result["txid"]

    async def notifications(self):
        async with self._lock:
            if not self._ws:
                self._ws = await websockets.connect(self.ws_url)
        try:
            while True:
                message = await self._ws.recv()
                yield message
        except websockets.ConnectionClosed:
            logger.warning("kaspa_ws_closed")
            self._ws = None

    async def close(self) -> None:
        await self._http.aclose()
        if self._ws:
            await self._ws.close()


