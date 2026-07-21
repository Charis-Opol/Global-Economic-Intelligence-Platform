from __future__ import annotations

import pandas as pd

from pipelines.warehouse.loader import LOADERS
from pipelines.warehouse.schema import create_schema


def test_load_dispatches_by_source_name(loader):
    # The string-keyed dispatch (the CLI's `--source`) reaches the same code
    # path as calling the method directly.
    loader.load(
        "coingecko",
        pd.DataFrame(
            {
                "coin_id": ["bitcoin"],
                "symbol": ["btc"],
                "name": ["Bitcoin"],
                "price_usd": [65000.0],
                "market_cap_usd": [1.28e12],
                "volume_usd": [2.5e10],
                "price_change_pct_24h": [1.5],
                "volatility_7d": [2.1],
                "logical_date": ["2026-07-20"],
            }
        ),
    )
    assert loader.con.execute("SELECT count(*) FROM fact_crypto").fetchone()[0] == 1


def test_unknown_source_is_rejected(loader):
    try:
        loader.load("nasdaq", pd.DataFrame())
    except ValueError as exc:
        assert "Unknown source" in str(exc)
    else:
        raise AssertionError("expected ValueError for an unknown source")


def test_loaders_cover_every_validated_source():
    # The warehouse can load exactly the sources the Step 9 validator checks.
    from pipelines.validation.suites import SUITE_BUILDERS

    assert set(LOADERS) == set(SUITE_BUILDERS)


def test_create_schema_is_idempotent(loader):
    # Re-applying the DDL to an already-populated warehouse is a no-op, not an
    # error - so the CLI can safely call it before every load.
    loader.load(
        "world_bank",
        pd.DataFrame(
            {
                "country_iso3": ["UGA"],
                "country_name": ["Uganda"],
                "indicator_id": ["NY.GDP.MKTP.CD"],
                "year": [2021],
                "gdp_usd": [4.0e10],
                "gdp_growth_rate": [0.081],
            }
        ),
    )
    create_schema(loader.con)  # again
    assert loader.con.execute("SELECT count(*) FROM fact_gdp").fetchone()[0] == 1


def test_conformed_date_dimension_is_shared_across_facts(loader):
    # A single 2026-07-20 row in dim_date serves crypto, exchange-rate, and
    # news facts - the point of a conformed dimension.
    day = "2026-07-20"
    loader.load(
        "coingecko",
        pd.DataFrame(
            {
                "coin_id": ["bitcoin"], "symbol": ["btc"], "name": ["Bitcoin"],
                "price_usd": [65000.0], "market_cap_usd": [1.28e12], "volume_usd": [2.5e10],
                "price_change_pct_24h": [1.5], "volatility_7d": [2.1], "logical_date": [day],
            }
        ),
    )
    loader.load(
        "exchange_rate",
        pd.DataFrame(
            {
                "base_code": ["USD"], "currency": ["UGX"], "rate": [3700.5],
                "exchange_momentum": [0.01], "logical_date": [day],
            }
        ),
    )

    # Both facts point at the one date row; join them through dim_date.
    combined = loader.con.execute(
        """
        SELECT d.full_date, cr.price_usd, fx.rate
        FROM dim_date d
        JOIN fact_crypto cr USING (date_key)
        JOIN fact_exchange_rate fx USING (date_key)
        WHERE d.full_date = DATE '2026-07-20'
        """
    ).fetchall()
    assert combined == [(pd.Timestamp(day).date(), 65000.0, 3700.5)]
    assert loader.con.execute("SELECT count(*) FROM dim_date").fetchone()[0] == 1
