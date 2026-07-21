from __future__ import annotations

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites.coingecko import build_suite


def test_valid_data_passes():
    df = pd.DataFrame(
        {
            "coin_id": ["bitcoin", "ethereum"],
            "symbol": ["btc", "eth"],
            "name": ["Bitcoin", "Ethereum"],
            "price_usd": [65000.0, 3400.0],
            "market_cap_usd": [1.2e12, 4.0e11],
            "volume_usd": [3.0e10, 1.5e10],
            "price_change_pct_24h": [1.2, -0.5],
            "volatility_7d": [2.1, None],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="coingecko")
    assert outcome.success


def test_catches_duplicate_and_negative_price():
    df = pd.DataFrame(
        {
            "coin_id": ["bitcoin", "bitcoin"],  # duplicate (coin, day)
            "symbol": ["btc", "btc"],
            "name": ["Bitcoin", "Bitcoin"],
            "price_usd": [65000.0, -1.0],  # negative price is invalid
            "market_cap_usd": [1.2e12, 1.2e12],
            "volume_usd": [3.0e10, 3.0e10],
            "price_change_pct_24h": [1.2, 1.2],
            "volatility_7d": [2.1, 2.1],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="coingecko")

    assert not outcome.success
    assert "expect_compound_columns_to_be_unique" in outcome.failed_expectations
    assert "expect_column_values_to_be_between" in outcome.failed_expectations
