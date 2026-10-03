"""Command line for trying the stash without Hermes: ``python -m stash scan``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import StashConfig
from .service import Stash
from .yields import solana_opportunities

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "pools.sample.json"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="stash", description=__doc__)
    parser.add_argument("--network", default="devnet")
    parser.add_argument("--home", default=None, help="state dir (default ~/.hermes/stash)")
    parser.add_argument(
        "--sample", action="store_true", help="use bundled sample pools instead of the live API"
    )
    parser.add_argument("--pools", type=Path, help="use pools from a DefiLlama-style JSON file")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("wallet")
    sub.add_parser("topup")
    sub.add_parser("scan")
    sub.add_parser("invest")
    sub.add_parser("checkup")
    sub.add_parser("portfolio")
    dep = sub.add_parser("deposit")
    dep.add_argument("usd", type=float)
    args = parser.parse_args(argv)

    cfg = StashConfig.from_dict({"network": args.network, "home": args.home})
    pools_file = args.pools or (SAMPLE if args.sample else None)
    if pools_file:
        pools = json.loads(pools_file.read_text())["data"]
        stash = Stash(cfg, scanner=lambda c: solana_opportunities(pools, c))
    else:
        stash = Stash(cfg)
    actions = {
        "wallet": stash.wallet_info,
        "topup": stash.request_topup,
        "scan": stash.scan,
        "invest": stash.invest,
        "checkup": stash.checkup,
        "portfolio": stash.portfolio,
        "deposit": lambda: stash.record_deposit(args.usd),
    }
    try:
        result = actions[args.cmd]()
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
