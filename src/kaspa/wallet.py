from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import structlog

from src.config import get_settings
from src.kaspa.rpc_client import KaspaRpcClient

logger = structlog.get_logger(__name__)


@dataclass
class KaspaUTXO:
    txid: str
    index: int
    amount: int
    script_public_key: str


class KaspaWallet:
    def __init__(self, rpc: KaspaRpcClient | None = None) -> None:
        self.settings = get_settings()
        self.rpc = rpc or KaspaRpcClient()

    async def balance(self) -> Dict[str, int]:
        return await self.rpc.get_balance(self.settings.kaspa_wallet_address)

    async def utxos(self) -> List[KaspaUTXO]:
        result = await self.rpc.get_utxos([self.settings.kaspa_wallet_address])
        utxos = [
            KaspaUTXO(
                txid=item["outpoint"]["transactionId"],
                index=item["outpoint"]["index"],
                amount=item["utxoEntry"]["amount"],
                script_public_key=item["utxoEntry"]["scriptPublicKey"]["scriptPublicKey"],
            )
            for item in result.get("entries", [])
        ]
        logger.debug("kaspa_utxos_loaded", count=len(utxos))
        return utxos

    async def submit_raw(self, raw_tx: str) -> str:
        txid = await self.rpc.submit_transaction(raw_tx)
        logger.info("kaspa_tx_submitted", txid=txid)
        return txid


