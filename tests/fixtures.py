JITOSOL = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
MSOL = "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So"
INF = "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def pool(pool_id, project, symbol, apy, tvl, mint, chain="Solana", exposure="single", il="no", stable=False):
    return {
        "pool": pool_id,
        "chain": chain,
        "project": project,
        "symbol": symbol,
        "apy": apy,
        "tvlUsd": tvl,
        "exposure": exposure,
        "ilRisk": il,
        "stablecoin": stable,
        "underlyingTokens": [mint],
    }


POOLS = [
    pool("kamino-usdc", "kamino-lend", "USDC", 8.4, 420_000_000, USDC, stable=True),
    pool("marginfi-usdc", "marginfi", "USDC", 7.1, 150_000_000, USDC, stable=True),
    pool("jito-jitosol", "jito-liquid-staking", "JITOSOL", 7.6, 2_100_000_000, JITOSOL),
    pool("marinade-msol", "marinade-liquid-staking", "MSOL", 7.2, 900_000_000, MSOL),
    pool("sanctum-inf", "sanctum-infinity", "INF", 8.0, 300_000_000, INF),
    pool("orca-sol-usdc", "orca-dex", "SOL-USDC", 24.0, 80_000_000, USDC, exposure="multi", il="yes"),
    pool("tiny-usdc", "tinyfarm", "USDC", 19.0, 200_000, USDC, stable=True),
    pool("degen-usdc", "degenvault", "USDC", 380.0, 30_000_000, USDC, stable=True),
    pool("aave-usdc", "aave-v3", "USDC", 9.0, 900_000_000, USDC, chain="Ethereum", stable=True),
]
