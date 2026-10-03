"""The five things the stash can do. Each returns a plain dict for the agent."""

from __future__ import annotations

from collections.abc import Callable

from . import strategy, topup, wallet, yields
from .config import StashConfig
from .executor import Executor, JupiterExecutor, PaperExecutor
from .ledger import Ledger
from .yields import Opportunity

Scanner = Callable[[StashConfig], list[Opportunity]]


class Stash:
    def __init__(
        self,
        cfg: StashConfig,
        scanner: Scanner = yields.scan,
        rpc: wallet.SolanaRpc | None = None,
        executor: Executor | None = None,
    ):
        self.cfg = cfg
        self.scanner = scanner
        self.keypair = wallet.load_or_create(cfg.home / "wallet.json")
        self.address = str(self.keypair.pubkey())
        self.rpc = rpc or wallet.SolanaRpc(cfg.rpc)
        self.ledger = Ledger.load(cfg.home / "ledger.json")
        if executor is None:
            live = not cfg.dry_run and cfg.network == "mainnet-beta"
            executor = JupiterExecutor(self.keypair, self.rpc, cfg.usdc_mint) if live else PaperExecutor()
        self.executor = executor

    @property
    def mode(self) -> str:
        return "paper" if isinstance(self.executor, PaperExecutor) else "live"

    def wallet_info(self) -> dict:
        info = {"address": self.address, "network": self.cfg.network, "mode": self.mode}
        try:
            info["sol"] = self.rpc.sol_balance(self.address)
            info["usdc"] = self.rpc.token_balance(self.address, self.cfg.usdc_mint)
        except Exception as exc:  # RPC hiccups should not break the conversation
            info["rpc_error"] = str(exc)
        return info

    def request_topup(self, usd: float | None = None) -> dict:
        usd = usd or self.cfg.topup_usd
        url = topup.solana_pay_url(self.address, usd, self.cfg.usdc_mint)
        return {"amount_usd": usd, "pay_url": url, "message": topup.topup_message(self.address, usd, url)}

    def record_deposit(self, usd: float) -> dict:
        self.ledger.deposit(usd)
        self.ledger.save()
        return self.portfolio()

    def scan(self, limit: int = 10) -> dict:
        opps = strategy.rank(self.scanner(self.cfg))
        return {"count": len(opps), "top": [o.to_dict() for o in opps[:limit]]}

    def invest(self) -> dict:
        cash = self.ledger.cash_usd
        if cash < 1:
            return {"invested": [], "note": "No idle cash. Ask the user for a top-up first."}
        plan = strategy.allocate(self.scanner(self.cfg), self.cfg)
        if not plan:
            return {"invested": [], "note": "No pool passed the filters today; keeping cash."}
        invested = []
        for alloc in plan:
            opp, usd = alloc.opportunity, round(cash * alloc.weight, 2)
            sig = self.executor.buy(opp.mint, usd)
            self.ledger.open(opp.pool_id, opp.project, opp.symbol, opp.apy, usd, opp.mint)
            invested.append({"label": opp.label, "usd": usd, "apy": opp.apy, "signature": sig})
        self.ledger.save()
        return {"invested": invested, "mode": self.mode, **self.portfolio()}

    def checkup(self, auto_rebalance: bool = True) -> dict:
        earned = self.ledger.accrue() if self.mode == "paper" else 0.0
        opps = self.scanner(self.cfg)
        moves = strategy.plan_rebalance(self.ledger.positions, opps, self.cfg)
        done = []
        if auto_rebalance:
            for move in moves:
                old = self.ledger.positions[move.from_pool]
                self.executor.sell(old.get("mint"), move.usd)
                usd = self.ledger.close(move.from_pool)
                self.executor.buy(move.to.mint, usd)
                self.ledger.open(
                    move.to.pool_id, move.to.project, move.to.symbol, move.to.apy, usd, move.to.mint
                )
                done.append(
                    {
                        "from": f"{old['symbol']} on {old['project']}",
                        "to": move.to.label,
                        "usd": round(usd, 2),
                        "reason": move.reason,
                    }
                )
        self.ledger.log("checkup", earned_usd=round(earned, 4), moves=len(done))
        self.ledger.save()
        return {
            "earned_since_last_check_usd": round(earned, 4),
            "rebalanced": done,
            "suggested": [] if auto_rebalance else [m.reason for m in moves],
            **self.portfolio(),
        }

    def portfolio(self) -> dict:
        led = self.ledger
        return {
            "deposited_usd": round(led.deposited_usd, 2),
            "cash_usd": round(led.cash_usd, 2) + 0.0,
            "total_usd": led.total_usd,
            "pnl_usd": round(led.total_usd - led.deposited_usd, 2),
            "positions": [
                {"label": f"{p['symbol']} on {p['project']}", "usd": round(p["usd"], 2), "apy": p["apy"]}
                for p in led.positions.values()
            ],
        }
