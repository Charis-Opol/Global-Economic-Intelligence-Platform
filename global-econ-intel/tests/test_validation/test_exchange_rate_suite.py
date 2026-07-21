from __future__ import annotations

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites.exchange_rate import build_suite


def test_valid_data_passes():
    df = pd.DataFrame(
        {
            "base_code": ["USD", "USD"],
            "currency": ["UGX", "EUR"],
            "rate": [3700.5, 0.92],
            "exchange_momentum": [0.01, None],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="exchange_rate")
    assert outcome.success


def test_catches_duplicate_pair_and_nonpositive_rate():
    df = pd.DataFrame(
        {
            "base_code": ["USD", "USD", "USD"],
            "currency": ["UGX", "UGX", "EUR"],  # (USD, UGX, same day) duplicated
            "rate": [3700.5, 3700.5, 0.0],  # zero rate is invalid
            "exchange_momentum": [0.01, 0.01, None],
            "logical_date": ["2026-07-20", "2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="exchange_rate")

    assert not outcome.success
    assert "expect_compound_columns_to_be_unique" in outcome.failed_expectations
    assert "expect_column_values_to_be_between" in outcome.failed_expectations
