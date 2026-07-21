from __future__ import annotations

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites.open_meteo import build_suite


def test_valid_data_passes():
    df = pd.DataFrame(
        {
            "date": ["2026-07-19", "2026-07-20"],
            "latitude": [0.3476, 0.3476],
            "longitude": [32.5825, 32.5825],
            "temp_max_c": [27.1, 26.8],
            "temp_min_c": [17.0, 16.5],
            "precipitation_mm": [0.0, 4.2],
            "precip_30d_avg_mm": [2.0, 2.1],
            "rainfall_anomaly_mm": [-2.0, 2.1],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="open_meteo")
    assert outcome.success


def test_catches_duplicate_date_and_out_of_range_values():
    df = pd.DataFrame(
        {
            "date": ["2026-07-20", "2026-07-20"],  # duplicate date
            "latitude": [0.3476, 95.0],  # invalid latitude
            "longitude": [32.5825, 32.5825],
            "temp_max_c": [27.1, 27.1],
            "temp_min_c": [17.0, 17.0],
            "precipitation_mm": [0.0, -3.0],  # negative precipitation
            "precip_30d_avg_mm": [2.0, 2.0],
            "rainfall_anomaly_mm": [-2.0, -5.0],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="open_meteo")

    assert not outcome.success
    assert "expect_column_values_to_be_unique" in outcome.failed_expectations
    assert "expect_column_values_to_be_between" in outcome.failed_expectations
