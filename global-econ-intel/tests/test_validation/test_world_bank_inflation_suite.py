from __future__ import annotations

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites.world_bank_inflation import build_suite


def test_valid_data_passes():
    df = pd.DataFrame(
        {
            "country_iso3": ["UGA", "UGA"],
            "country_name": ["Uganda", "Uganda"],
            "indicator_id": ["FP.CPI.TOTL.ZG"] * 2,
            "year": [2022, 2023],
            "inflation_pct": [5.0, 7.5],
            "inflation_trend": [None, 2.5],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="world_bank_inflation")
    assert outcome.success


def test_catches_duplicate_key_and_out_of_range_value():
    df = pd.DataFrame(
        {
            "country_iso3": ["UGA", "UGA", "UGA"],
            "country_name": ["Uganda", "Uganda", "Uganda"],
            "indicator_id": ["FP.CPI.TOTL.ZG"] * 3,
            "year": [2023, 2023, 2024],  # (UGA, FP.CPI.TOTL.ZG, 2023) duplicated
            "inflation_pct": [5.0, 5.0, 9999.0],  # implausible outlier
            "inflation_trend": [None, None, 9994.0],
            "logical_date": ["2026-07-20", "2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="world_bank_inflation")

    assert not outcome.success
    assert "expect_compound_columns_to_be_unique" in outcome.failed_expectations
    assert "expect_column_values_to_be_between" in outcome.failed_expectations
