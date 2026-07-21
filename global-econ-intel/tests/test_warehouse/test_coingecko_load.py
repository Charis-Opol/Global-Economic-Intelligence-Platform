from __future__ import annotations

import pandas as pd


def _silver() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "coin_id": ["bitcoin", "ethereum"],
            "symbol": ["btc", "eth"],
            "name": ["Bitcoin", "Ethereum"],
            "price_usd": [65000.0, 3200.0],
            "market_cap_usd": [1.28e12, 3.85e11],
            "volume_usd": [2.5e10, 1.2e10],
            "price_change_pct_24h": [1.5, -0.8],
            "volatility_7d": [2.1, 3.4],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )


def test_loads_coins_and_price_facts(loader):
    loader.load_coingecko(_silver())

    coins = loader.con.execute(
        "SELECT coin_id, symbol, name FROM dim_coin ORDER BY coin_id"
    ).fetchall()
    assert coins == [("bitcoin", "btc", "Bitcoin"), ("ethereum", "eth", "Ethereum")]

    btc = loader.con.execute(
        """
        SELECT f.price_usd, f.volatility_7d
        FROM fact_crypto f JOIN dim_coin c USING (coin_key)
        WHERE c.coin_id = 'bitcoin'
        """
    ).fetchone()
    assert btc == (65000.0, 2.1)


def test_next_day_adds_a_row_without_duplicating_the_coin(loader):
    loader.load_coingecko(_silver())

    next_day = _silver()
    next_day["logical_date"] = "2026-07-21"
    next_day["price_usd"] = [66000.0, 3250.0]
    loader.load_coingecko(next_day)

    # Same two coins, but now two daily snapshots each.
    assert loader.con.execute("SELECT count(*) FROM dim_coin").fetchone()[0] == 2
    assert loader.con.execute("SELECT count(*) FROM fact_crypto").fetchone()[0] == 4
    assert loader.con.execute("SELECT count(*) FROM dim_date").fetchone()[0] == 2
