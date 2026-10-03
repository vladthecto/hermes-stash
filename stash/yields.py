"""Scan Solana yield opportunities from the DefiLlama yields aggregator."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import httpx

from .config import StashConfig

POOLS_URL = "https://yields.llama.fi/pools"


@dataclass(frozen=True)
class Opportunity:
    pool_id: str
    project: str
    symbol: str
    apy: float
    tvl_usd: float
    stablecoin: bool
    mint: str | None

    @property
    def label(self) -> str:
        return f"{self.symbol} on {self.project}"

    def to_dict(self) -> dict:
        return asdict(self) | {"label": self.label}


def fetch_pools(client: httpx.Client | None = None) -> list[dict]:
    client = client or httpx.Client(timeout=30)
    resp = client.get(POOLS_URL)
    resp.raise_for_status()
    return resp.json()["data"]


def solana_opportunities(pools: list[dict], cfg: StashConfig) -> list[Opportunity]:
    """Keep simple, single-asset Solana pools that are big enough and not suspicious."""
    found = []
    for pool in pools:
        if pool.get("chain") != "Solana":
            continue
        if pool.get("exposure") != "single" or pool.get("ilRisk") == "yes":
            continue
        apy = pool.get("apy") or 0.0
        tvl = pool.get("tvlUsd") or 0.0
        if tvl < cfg.min_tvl_usd or not cfg.min_apy <= apy <= cfg.max_apy:
            continue
        tokens = pool.get("underlyingTokens") or []
        found.append(
            Opportunity(
                pool_id=pool["pool"],
                project=pool["project"],
                symbol=pool["symbol"],
                apy=round(apy, 2),
                tvl_usd=tvl,
                stablecoin=bool(pool.get("stablecoin")),
                mint=tokens[0] if tokens else None,
            )
        )
    return found


def scan(cfg: StashConfig, client: httpx.Client | None = None) -> list[Opportunity]:
    return solana_opportunities(fetch_pools(client), cfg)
