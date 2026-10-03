"""The stash's own wallet: a local keypair plus a couple of RPC reads."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from solders.keypair import Keypair

LAMPORTS_PER_SOL = 1_000_000_000


def load_or_create(path: Path) -> Keypair:
    """Load the keypair at ``path``, creating one (mode 0600) on first use."""
    if path.exists():
        return Keypair.from_bytes(bytes(json.loads(path.read_text())))
    path.parent.mkdir(parents=True, exist_ok=True)
    keypair = Keypair()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(list(bytes(keypair)), fh)
    return keypair


class SolanaRpc:
    def __init__(self, url: str, client: httpx.Client | None = None):
        self.url = url
        self.client = client or httpx.Client(timeout=15)

    def call(self, method: str, *params):
        resp = self.client.post(
            self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}
        )
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise RuntimeError(f"{method}: {body['error'].get('message', body['error'])}")
        return body["result"]

    def sol_balance(self, owner: str) -> float:
        return self.call("getBalance", owner)["value"] / LAMPORTS_PER_SOL

    def token_balance(self, owner: str, mint: str) -> float:
        result = self.call("getTokenAccountsByOwner", owner, {"mint": mint}, {"encoding": "jsonParsed"})
        return sum(
            float(acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"] or 0)
            for acc in result["value"]
        )

    def send_transaction(self, raw_b64: str) -> str:
        return self.call("sendTransaction", raw_b64, {"encoding": "base64", "maxRetries": 3})
