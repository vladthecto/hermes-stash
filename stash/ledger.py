"""A small JSON ledger of deposits, positions and history."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Ledger:
    path: Path
    deposited_usd: float = 0.0
    cash_usd: float = 0.0
    positions: dict[str, dict] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: now().isoformat())

    @classmethod
    def load(cls, path: Path) -> Ledger:
        if not path.exists():
            return cls(path)
        return cls(path, **json.loads(path.read_text()))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v for k, v in self.__dict__.items() if k != "path"}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.path)

    @property
    def total_usd(self) -> float:
        return round(self.cash_usd + sum(p["usd"] for p in self.positions.values()), 2)

    def log(self, event: str, **details) -> None:
        self.history.append({"at": now().isoformat(), "event": event, **details})

    def deposit(self, usd: float) -> None:
        self.deposited_usd += usd
        self.cash_usd += usd
        self.log("deposit", usd=usd)

    def open(self, pool_id: str, project: str, symbol: str, apy: float, usd: float, mint: str | None) -> None:
        pos = self.positions.setdefault(
            pool_id, {"project": project, "symbol": symbol, "apy": apy, "usd": 0.0, "mint": mint}
        )
        pos["usd"] = round(pos["usd"] + usd, 2)
        pos["apy"] = apy
        self.cash_usd = round(self.cash_usd - usd, 2)
        self.log("invest", pool=pool_id, label=f"{symbol} on {project}", usd=usd, apy=apy)

    def close(self, pool_id: str) -> float:
        usd = self.positions.pop(pool_id)["usd"]
        self.cash_usd = round(self.cash_usd + usd, 2)
        self.log("withdraw", pool=pool_id, usd=usd)
        return usd

    def accrue(self, at: datetime | None = None) -> float:
        """Grow paper positions by their APY since the last update. Returns USD earned."""
        at = at or now()
        days = (at - datetime.fromisoformat(self.updated_at)).total_seconds() / 86400
        earned = 0.0
        if days > 0:
            for pos in self.positions.values():
                grown = pos["usd"] * (1 + pos["apy"] / 100) ** (days / 365)
                earned += grown - pos["usd"]
                pos["usd"] = round(grown, 6)
        self.updated_at = at.isoformat()
        return round(earned, 6)
