"""Great Expectations suite for the Open-Meteo Silver dataset (Day 1, Step 9)."""
from __future__ import annotations

import great_expectations as gx
from great_expectations import expectations as gxe

COLUMNS = [
    "date",
    "latitude",
    "longitude",
    "temp_max_c",
    "temp_min_c",
    "precipitation_mm",
    "precip_30d_avg_mm",
    "rainfall_anomaly_mm",
    "logical_date",
]


def build_suite() -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="open_meteo_silver")

    suite.add_expectation(gxe.ExpectTableColumnsToMatchSet(column_set=COLUMNS))

    for column in ["date", "latitude", "longitude", "logical_date"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    # Duplicates: one row per calendar day.
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="date"))

    # Ranges
    suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="latitude", min_value=-90, max_value=90))
    suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="longitude", min_value=-180, max_value=180))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="precipitation_mm", min_value=0, max_value=None)
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="temp_max_c", min_value=-30, max_value=60)
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="temp_min_c", min_value=-50, max_value=50)
    )

    return suite
