import json
from datetime import timedelta

import pytest
from fixtures import POOLS

from stash.config import StashConfig
from stash.ledger import now
from stash.service import Stash
from stash.yields import solana_opportunities


class FakeRpc:
    def sol_balance(self, owner):
        return 0.05

    def token_balance(self, owner, mint):
        return 100.0


@pytest.fixture
def stash(tmp_path):
    cfg = StashConfig(home=tmp_path)
    return Stash(cfg, scanner=lambda c: solana_opportunities(POOLS, c), rpc=FakeRpc())


def test_wallet_is_created_once_with_private_permissions(stash, tmp_path):
    key = tmp_path / "wallet.json"
    assert key.stat().st_mode & 0o777 == 0o600
    again = Stash(stash.cfg, scanner=stash.scanner, rpc=FakeRpc())
    assert again.address == stash.address
    assert stash.wallet_info()["usdc"] == 100.0


def test_topup_is_a_solana_pay_link(stash):
    req = stash.request_topup()
    assert req["pay_url"].startswith(f"solana:{stash.address}?amount=100")
    assert stash.cfg.usdc_mint in req["pay_url"]


def test_full_cycle_deposit_invest_checkup(stash):
    assert stash.invest()["invested"] == []
    stash.record_deposit(100)
    result = stash.invest()
    assert result["mode"] == "paper"
    assert len(result["invested"]) == 3
    assert result["cash_usd"] == pytest.approx(0, abs=0.05)

    stash.ledger.updated_at = (now() - timedelta(days=30)).isoformat()
    report = stash.checkup()
    assert report["earned_since_last_check_usd"] > 0.5
    assert report["pnl_usd"] > 0
    assert report["rebalanced"] == []

    saved = json.loads((stash.cfg.home / "ledger.json").read_text())
    assert [e["event"] for e in saved["history"]][:2] == ["deposit", "invest"]


def test_plugin_tools_return_json_errors_instead_of_raising(stash):
    import importlib.util
    import pathlib
    import sys

    root = pathlib.Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "hermes_stash_plugin", root / "__init__.py", submodule_search_locations=[str(root)]
    )
    plugin = importlib.util.module_from_spec(spec)
    sys.modules["hermes_stash_plugin"] = plugin
    spec.loader.exec_module(plugin)

    registered = {}

    class Ctx:
        def get_config(self, key, default=None):
            return {"network": "devnet"}.get(key, default)

        def register_tool(self, name, toolset, schema, handler):
            registered[name] = handler

        def register_command(self, name, handler, description):
            registered["/" + name] = handler

    plugin.register(Ctx())
    sys.modules["hermes_stash_plugin.tools"].bind(stash)
    assert set(registered) >= {"stash_scan", "stash_invest", "/stash"}
    assert json.loads(registered["stash_scan"]({"limit": 2}))["count"] == 5
    assert "error" in json.loads(registered["stash_record_deposit"]({}))
