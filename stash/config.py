"""User-facing settings for the stash."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

RPC_URLS = {
    "mainnet-beta": "https://api.mainnet-beta.solana.com",
    "devnet": "https://api.devnet.solana.com",
}

# Circle USDC mints.
USDC_MINTS = {
    "mainnet-beta": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "devnet": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
}


@dataclass
class StashConfig:
    network: str = "devnet"
    rpc_url: str | None = None
    home: Path = field(default_factory=lambda: Path.home() / ".hermes" / "stash")
    topup_usd: float = 100.0
    max_positions: int = 3
    max_weight: float = 0.5
    min_tvl_usd: float = 5_000_000
    min_apy: float = 2.0
    max_apy: float = 40.0
    rebalance_threshold: float = 1.5
    dry_run: bool = True

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> StashConfig:
        raw = raw or {}
        known = {f.name for f in fields(cls)}
        values = {k: v for k, v in raw.items() if k in known and v is not None}
        if "home" in values:
            values["home"] = Path(values["home"]).expanduser()
        cfg = cls(**values)
        if cfg.network not in RPC_URLS:
            raise ValueError(f"unknown network {cfg.network!r}, use one of {sorted(RPC_URLS)}")
        return cfg

    @property
    def rpc(self) -> str:
        return self.rpc_url or RPC_URLS[self.network]

    @property
    def usdc_mint(self) -> str:
        return USDC_MINTS[self.network]
