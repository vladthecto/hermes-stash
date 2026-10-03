import pytest
from fixtures import POOLS

from stash import strategy
from stash.config import StashConfig
from stash.yields import solana_opportunities

CFG = StashConfig()


def test_filters_keep_only_safe_solana_single_asset_pools():
    ids = {o.pool_id for o in solana_opportunities(POOLS, CFG)}
    assert ids == {"kamino-usdc", "marginfi-usdc", "jito-jitosol", "marinade-msol", "sanctum-inf"}


def test_allocation_is_diverse_capped_and_sums_to_one():
    plan = strategy.allocate(solana_opportunities(POOLS, CFG), CFG)
    assert len(plan) == CFG.max_positions
    assert len({a.opportunity.project for a in plan}) == len(plan)
    assert all(a.weight <= CFG.max_weight for a in plan)
    assert sum(a.weight for a in plan) == pytest.approx(1, abs=1e-3)


def test_allocation_caps_a_dominant_pool():
    cfg = StashConfig(max_positions=2, max_weight=0.6)
    opps = solana_opportunities(POOLS, cfg)
    boosted = [o if o.pool_id != "kamino-usdc" else o.__class__(**{**o.__dict__, "apy": 39.0}) for o in opps]
    plan = {a.opportunity.pool_id: a.weight for a in strategy.allocate(boosted, cfg)}
    assert plan["kamino-usdc"] == pytest.approx(0.6)


def test_rebalance_moves_out_of_a_lagging_or_vanished_pool():
    opps = solana_opportunities(POOLS, CFG)
    positions = {
        "marinade-msol": {"project": "marinade-liquid-staking", "usd": 50.0},
        "gone-pool": {"project": "gone", "usd": 20.0},
    }
    moves = strategy.plan_rebalance(positions, opps, StashConfig(rebalance_threshold=0.5))
    reasons = {m.from_pool: m.reason for m in moves}
    assert reasons["gone-pool"] == "pool no longer qualifies"
    assert "->" in reasons["marinade-msol"]
    assert len({m.to.project for m in moves}) == len(moves)


def test_rebalance_holds_when_the_gap_is_small():
    opps = solana_opportunities(POOLS, CFG)
    positions = {"kamino-usdc": {"project": "kamino-lend", "usd": 50.0}}
    assert strategy.plan_rebalance(positions, opps, CFG) == []
