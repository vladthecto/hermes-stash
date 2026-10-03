"""Tool schemas shown to the model."""

_NO_ARGS = {"type": "object", "properties": {}}

STASH_WALLET = {
    "name": "stash_wallet",
    "description": "Show the stash wallet address, network, mode (paper/live) and SOL/USDC balances.",
    "parameters": _NO_ARGS,
}

STASH_REQUEST_TOPUP = {
    "name": "stash_request_topup",
    "description": "Build a Solana Pay link asking the user to top up the stash (default $100 USDC). "
    "Send the returned message to the user as is.",
    "parameters": {
        "type": "object",
        "properties": {"usd": {"type": "number", "description": "Amount in USD, defaults to config"}},
    },
}

STASH_RECORD_DEPOSIT = {
    "name": "stash_record_deposit",
    "description": "Record that the user topped up the stash, making the cash available to invest.",
    "parameters": {
        "type": "object",
        "properties": {"usd": {"type": "number", "description": "Amount received in USD"}},
        "required": ["usd"],
    },
}

STASH_SCAN = {
    "name": "stash_scan",
    "description": "Scan Solana yield aggregators and return the best single-asset pools, ranked.",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "How many pools to return", "default": 10}
        },
    },
}

STASH_INVEST = {
    "name": "stash_invest",
    "description": "Invest all idle cash across the top pools (one per protocol, capped weights).",
    "parameters": _NO_ARGS,
}

STASH_CHECKUP = {
    "name": "stash_checkup",
    "description": "Daily health check: accrue yield, rescan pools and move money out of pools that "
    "dropped out or fell behind the best option.",
    "parameters": {
        "type": "object",
        "properties": {
            "auto_rebalance": {
                "type": "boolean",
                "description": "Execute moves (true) or only suggest them (false)",
                "default": True,
            }
        },
    },
}

STASH_PORTFOLIO = {
    "name": "stash_portfolio",
    "description": "Show deposits, cash, positions and PnL.",
    "parameters": _NO_ARGS,
}

ALL = [
    STASH_WALLET,
    STASH_REQUEST_TOPUP,
    STASH_RECORD_DEPOSIT,
    STASH_SCAN,
    STASH_INVEST,
    STASH_CHECKUP,
    STASH_PORTFOLIO,
]
