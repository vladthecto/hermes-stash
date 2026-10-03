"""Top-up requests as Solana Pay transfer links."""

from __future__ import annotations

from urllib.parse import urlencode


def solana_pay_url(recipient: str, amount: float, spl_token: str, label: str = "Hermes Stash") -> str:
    query = urlencode(
        {
            "amount": f"{amount:g}",
            "spl-token": spl_token,
            "label": label,
            "message": f"Top up your Hermes Stash with ${amount:g}",
        }
    )
    return f"solana:{recipient}?{query}"


def topup_message(recipient: str, amount: float, url: str) -> str:
    return (
        f"Time to feed the stash: please send ${amount:g} USDC to {recipient}.\n"
        f"One-tap link (Phantom, Solflare, Backpack): {url}"
    )
