from __future__ import annotations

import tempfile
from pathlib import Path

import mlflow
import pandas as pd
import pytest

from pipelines.warehouse.loader import WarehouseLoader
from pipelines.warehouse.schema import connect, create_schema


@pytest.fixture
def mlflow_tracking():
    """Points mlflow at a local sqlite-backed tracking store instead of a
    live server - sqlite is a database-backed store, so (unlike a plain file
    store) it fully supports the Model Registry, same as the Postgres-backed
    store the real deployment uses. tempfile.mkdtemp rather than pytest's
    tmp_path fixture: this Windows environment sometimes denies access to
    pytest's shared base temp dir between runs.
    """
    d = Path(tempfile.mkdtemp())
    mlflow.set_tracking_uri(f"sqlite:///{d / 'mlflow.db'}")
    yield d


@pytest.fixture
def warehouse():
    """An in-memory warehouse with enough history per entity (2 countries x
    4 years, 2 currency pairs x 8 days, 2 coins x 8 days) for every forecast
    spec to clear MIN_TRAINING_ROWS after the first-observation-per-entity
    row is dropped for its null lag feature."""
    con = connect(":memory:")
    create_schema(con)
    loader = WarehouseLoader(con)

    years = [2020, 2021, 2022, 2023]
    loader.load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA"] * 4 + ["KEN"] * 4,
                "country_name": ["Uganda"] * 4 + ["Kenya"] * 4,
                "indicator_id": ["NY.GDP.MKTP.CD"] * 8,
                "year": years * 2,
                "gdp_usd": [37e9, 40e9, 44e9, 47e9, 90e9, 95e9, 99e9, 103e9],
                "gdp_growth_rate": [None, 0.08, 0.10, 0.07] * 2,
            }
        )
    )
    loader.load_world_bank_inflation(
        pd.DataFrame(
            {
                "country_iso3": ["UGA"] * 4 + ["KEN"] * 4,
                "country_name": ["Uganda"] * 4 + ["Kenya"] * 4,
                "indicator_id": ["FP.CPI.TOTL.ZG"] * 8,
                "year": years * 2,
                "inflation_pct": [4.0, 5.0, 7.5, 6.0, 5.5, 6.5, 8.0, 7.0],
                "inflation_trend": [None, 1.0, 2.5, -1.5] * 2,
            }
        )
    )

    days = [f"2026-07-{d:02d}" for d in range(10, 18)]  # 8 days
    loader.load_exchange_rate(
        pd.DataFrame(
            {
                "base_code": ["USD"] * 16,
                "currency": ["UGX"] * 8 + ["EUR"] * 8,
                "rate": [3700 + i * 2 for i in range(8)] + [0.90 + i * 0.001 for i in range(8)],
                "exchange_momentum": [None] + [0.001] * 7 + [None] + [0.0001] * 7,
                "logical_date": days * 2,
            }
        )
    )
    loader.load_coingecko(
        pd.DataFrame(
            {
                "coin_id": ["bitcoin"] * 8 + ["ethereum"] * 8,
                "symbol": ["btc"] * 8 + ["eth"] * 8,
                "name": ["Bitcoin"] * 8 + ["Ethereum"] * 8,
                "price_usd": [60000 + i * 500 for i in range(8)]
                + [3000 + i * 20 for i in range(8)],
                "market_cap_usd": [1.2e12] * 16,
                "volume_usd": [2.5e10] * 16,
                "price_change_pct_24h": [1.0] * 16,
                "volatility_7d": [None] * 2 + [2.0] * 14,
                "logical_date": days * 2,
            }
        )
    )

    try:
        yield con
    finally:
        con.close()
