from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

# The backend is its own deployable service (own Dockerfile/requirements.txt
# copying only `app/`), so `app.*` is only importable with backend/ itself on
# sys.path - the same reason tests/test_spark/conftest.py adds spark/jobs.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from pipelines.warehouse.loader import WarehouseLoader  # noqa: E402
from pipelines.warehouse.schema import connect, create_schema  # noqa: E402

from app.db import get_connection  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def warehouse():
    """An in-memory star schema preloaded with a small fixture spanning all
    five domains, built with the same Step 10 loader that populates the real
    warehouse - so these tests exercise the real schema, not a hand-rolled
    stand-in for it."""
    con = connect(":memory:")
    create_schema(con)
    loader = WarehouseLoader(con)

    loader.load_world_bank(
        pd.DataFrame(
            {
                "country_iso3": ["UGA", "UGA", "KEN"],
                "country_name": ["Uganda", "Uganda", "Kenya"],
                "indicator_id": ["NY.GDP.MKTP.CD"] * 3,
                "year": [2020, 2021, 2021],
                "gdp_usd": [3.7e10, 4.0e10, 1.1e11],
                "gdp_growth_rate": [None, 0.081, 0.05],
            }
        )
    )
    loader.load_exchange_rate(
        pd.DataFrame(
            {
                "base_code": ["USD", "USD"],
                "currency": ["UGX", "EUR"],
                "rate": [3700.5, 0.92],
                "exchange_momentum": [0.01, None],
                "logical_date": ["2026-07-20", "2026-07-20"],
            }
        )
    )
    loader.load_open_meteo(
        pd.DataFrame(
            {
                "date": ["2026-07-19", "2026-07-20"],
                "latitude": [0.3476, 0.3476],
                "longitude": [32.5825, 32.5825],
                "temp_max_c": [27.1, 26.4],
                "temp_min_c": [17.0, 16.8],
                "precipitation_mm": [2.5, 0.0],
                "precip_30d_avg_mm": [3.1, 3.0],
                "rainfall_anomaly_mm": [-0.6, -3.0],
                "logical_date": ["2026-07-20", "2026-07-20"],
            }
        )
    )
    loader.load_coingecko(
        pd.DataFrame(
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
    )
    loader.load_newsapi(
        pd.DataFrame(
            {
                "source_name": ["Reuters", None],  # second article has no source name
                "author": ["Jane Doe", None],
                "title": ["Markets rally", "Op-ed on trade"],
                "description": ["...", None],
                "url": ["https://ex.com/a", "https://ex.com/b"],
                "published_at": ["2026-07-20T09:00:00Z", "2026-07-20T11:30:00Z"],
                "articles_that_day": [2, 2],
                "logical_date": ["2026-07-20", "2026-07-20"],
            }
        )
    )
    loader.load_world_bank_inflation(
        pd.DataFrame(
            {
                "country_iso3": ["UGA", "UGA", "KEN"],
                "country_name": ["Uganda", "Uganda", "Kenya"],
                "indicator_id": ["FP.CPI.TOTL.ZG"] * 3,
                "year": [2020, 2021, 2021],
                "inflation_pct": [4.0, 5.0, 6.1],
                "inflation_trend": [None, 1.0, None],
            }
        )
    )

    try:
        yield con
    finally:
        con.close()


@pytest.fixture
def client(warehouse):
    """A TestClient wired to the fixture warehouse instead of a real file."""
    app.dependency_overrides[get_connection] = lambda: warehouse
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_connection, None)
