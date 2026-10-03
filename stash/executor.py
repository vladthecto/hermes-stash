"""Turn decisions into trades.

``PaperExecutor`` only writes to the ledger and is the default. ``JupiterExecutor``
swaps USDC into yield-bearing tokens (LSTs and friends) through Jupiter on mainnet.
"""

from __future__ import annotations

import base64
from typing import Protocol

import httpx
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

from .wallet import SolanaRpc

JUPITER_API = "https://lite-api.jup.ag/swap/v1"
USDC_DECIMALS = 6


class Executor(Protocol):
    def buy(self, mint: str | None, usd: float) -> str | None: ...

    def sell(self, mint: str | None, usd: float) -> str | None: ...


class PaperExecutor:
    """Simulated fills. Returns no signature."""

    def buy(self, mint: str | None, usd: float) -> str | None:
        return None

    def sell(self, mint: str | None, usd: float) -> str | None:
        return None


class JupiterExecutor:
    def __init__(
        self,
        keypair: Keypair,
        rpc: SolanaRpc,
        usdc_mint: str,
        slippage_bps: int = 50,
        client: httpx.Client | None = None,
    ):
        self.keypair = keypair
        self.rpc = rpc
        self.usdc_mint = usdc_mint
        self.slippage_bps = slippage_bps
        self.client = client or httpx.Client(timeout=30)

    def buy(self, mint: str | None, usd: float) -> str | None:
        if not mint or mint == self.usdc_mint:
            return None  # already USDC: lending deposits are tracked on paper in v0.1
        return self._swap(self.usdc_mint, mint, int(usd * 10**USDC_DECIMALS), exact_out=False)

    def sell(self, mint: str | None, usd: float) -> str | None:
        if not mint or mint == self.usdc_mint:
            return None
        return self._swap(mint, self.usdc_mint, int(usd * 10**USDC_DECIMALS), exact_out=True)

    def _swap(self, input_mint: str, output_mint: str, amount: int, exact_out: bool) -> str:
        quote = self.client.get(
            f"{JUPITER_API}/quote",
            params={
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": self.slippage_bps,
                "swapMode": "ExactOut" if exact_out else "ExactIn",
            },
        )
        quote.raise_for_status()
        swap = self.client.post(
            f"{JUPITER_API}/swap",
            json={
                "quoteResponse": quote.json(),
                "userPublicKey": str(self.keypair.pubkey()),
                "dynamicComputeUnitLimit": True,
            },
        )
        swap.raise_for_status()
        unsigned = VersionedTransaction.from_bytes(base64.b64decode(swap.json()["swapTransaction"]))
        signed = VersionedTransaction(unsigned.message, [self.keypair])
        return self.rpc.send_transaction(base64.b64encode(bytes(signed)).decode())
