"""Pick where the money goes, and decide when to move it.

The strategy is intentionally boring: prefer high APY, discount small pools,
spread across protocols, and only move money when the gap is worth it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .config import StashConfig
from .yields import Opportunity


@dataclass(frozen=True)
class Allocation:
    opportunity: Opportunity
    weight: float


@dataclass(frozen=True)
class Move:
    from_pool: str
    to: Opportunity
    usd: float
    reason: str


def score(opp: Opportunity) -> float:
    """APY scaled by a gentle size bonus: a $500M pool beats a $5M one at equal APY."""
    return opp.apy * math.log10(max(opp.tvl_usd, 10))


def rank(opps: list[Opportunity]) -> list[Opportunity]:
    return sorted(opps, key=score, reverse=True)


def allocate(opps: list[Opportunity], cfg: StashConfig) -> list[Allocation]:
    """Top pools, at most one per protocol, weighted by score and capped at ``max_weight``."""
    picked: list[Opportunity] = []
    for opp in rank(opps):
        if opp.project in {p.project for p in picked}:
            continue
        picked.append(opp)
        if len(picked) == cfg.max_positions:
            break
    if not picked:
        return []

    cap = max(cfg.max_weight, 1 / len(picked))
    weights = {p.pool_id: score(p) for p in picked}
    # Water-fill: clip anything above the cap and share the excess with the rest.
    fixed: dict[str, float] = {}
    while True:
        free = {k: v for k, v in weights.items() if k not in fixed}
        budget = 1 - sum(fixed.values())
        total = sum(free.values())
        over = {k for k, v in free.items() if v / total * budget > cap}
        if not over:
            fixed.update({k: v / total * budget for k, v in free.items()})
            break
        fixed.update({k: cap for k in over})
    return [Allocation(p, round(fixed[p.pool_id], 4)) for p in picked]


def plan_rebalance(positions: dict[str, dict], opps: list[Opportunity], cfg: StashConfig) -> list[Move]:
    """Move a position when its pool vanished or the best pool beats it by ``rebalance_threshold``."""
    if not opps:
        return []
    by_id = {o.pool_id: o for o in opps}
    held_projects = {p["project"] for p in positions.values()}
    moves = []
    for pool_id, pos in positions.items():
        current = by_id.get(pool_id)
        candidates = [
            o
            for o in rank(opps)
            if o.pool_id != pool_id and (o.project == pos["project"] or o.project not in held_projects)
        ]
        if not candidates:
            continue
        best = candidates[0]
        if current is None:
            moves.append(Move(pool_id, best, pos["usd"], "pool no longer qualifies"))
        elif best.apy - current.apy >= cfg.rebalance_threshold:
            moves.append(Move(pool_id, best, pos["usd"], f"APY {current.apy:.2f}% -> {best.apy:.2f}%"))
        else:
            continue
        held_projects.add(best.project)
    return moves
