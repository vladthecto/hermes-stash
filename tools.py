"""Tool handlers: thin JSON wrappers around ``stash.service.Stash``."""

from __future__ import annotations

import json
from collections.abc import Callable

from .stash.service import Stash

_stash: Stash | None = None


def bind(stash: Stash) -> None:
    global _stash
    _stash = stash


def _run(fn: Callable[[Stash], dict]) -> str:
    if _stash is None:
        return json.dumps({"error": "hermes-stash is not initialised"})
    try:
        return json.dumps(fn(_stash))
    except Exception as exc:  # handlers must never raise
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


def stash_wallet(args: dict, **kwargs) -> str:
    return _run(lambda s: s.wallet_info())


def stash_request_topup(args: dict, **kwargs) -> str:
    return _run(lambda s: s.request_topup(args.get("usd")))


def stash_record_deposit(args: dict, **kwargs) -> str:
    return _run(lambda s: s.record_deposit(float(args["usd"])))


def stash_scan(args: dict, **kwargs) -> str:
    return _run(lambda s: s.scan(int(args.get("limit", 10))))


def stash_invest(args: dict, **kwargs) -> str:
    return _run(lambda s: s.invest())


def stash_checkup(args: dict, **kwargs) -> str:
    return _run(lambda s: s.checkup(bool(args.get("auto_rebalance", True))))


def stash_portfolio(args: dict, **kwargs) -> str:
    return _run(lambda s: s.portfolio())
