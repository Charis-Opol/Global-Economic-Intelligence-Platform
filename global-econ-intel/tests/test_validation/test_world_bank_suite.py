from __future__ import annotations

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites.world_bank import build_suite


def test_valid_data_passes():
    df = pd.DataFrame(
        {
            "country_iso3": ["UGA", "KEN"],
            "country_name": ["Uganda", "Kenya"],
            "indicator_id": ["NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD"],
            "year": [2023, 2023],
            "gdp_usd": [48_000_000_000.0, 110_000_000_000.0],
            "gdp_growth_rate": [0.05, None],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="world_bank")
    assert outcome.success


def test_catches_null_duplicate_and_range_violations():
    df = pd.DataFrame(
        {
            "country_iso3": ["UGA", "UGA", None],  # null identifying field
            "country_name": ["Uganda", "Uganda", "Nowhere"],
            "indicator_id": ["NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD"],
            "year": [2023, 2023, 1800],  # duplicate (UGA, indicator, 2023) + out-of-range year
            "gdp_usd": [48_000_000_000.0, 48_000_000_000.0, -5.0],  # negative GDP
            "gdp_growth_rate": [0.05, 0.05, None],
            "logical_date": ["2026-07-20", "2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="world_bank")

    assert not outcome.success
    assert "expect_column_values_to_not_be_null" in outcome.failed_expectations
    assert "expect_compound_columns_to_be_unique" in outcome.failed_expectations
    assert "expect_column_values_to_be_between" in outcome.failed_expectations
