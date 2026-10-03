"""Registers the Hermes Stash tools and the /stash command."""

from . import schemas, tools
from .stash.config import StashConfig
from .stash.service import Stash

_CONFIG_KEYS = (
    "network",
    "rpc_url",
    "topup_usd",
    "max_positions",
    "min_tvl_usd",
    "rebalance_threshold",
    "dry_run",
)

_HANDLERS = {
    "stash_wallet": tools.stash_wallet,
    "stash_request_topup": tools.stash_request_topup,
    "stash_record_deposit": tools.stash_record_deposit,
    "stash_scan": tools.stash_scan,
    "stash_invest": tools.stash_invest,
    "stash_checkup": tools.stash_checkup,
    "stash_portfolio": tools.stash_portfolio,
}


def register(ctx):
    raw = {key: ctx.get_config(key, default=None) for key in _CONFIG_KEYS}
    raw["rpc_url"] = raw["rpc_url"] or None
    tools.bind(Stash(StashConfig.from_dict(raw)))

    for schema in schemas.ALL:
        ctx.register_tool(
            name=schema["name"],
            toolset="stash",
            schema=schema,
            handler=_HANDLERS[schema["name"]],
        )

    ctx.register_command(
        "stash",
        handler=lambda raw_args: tools.stash_portfolio({}),
        description="Show the Hermes Stash portfolio",
    )
