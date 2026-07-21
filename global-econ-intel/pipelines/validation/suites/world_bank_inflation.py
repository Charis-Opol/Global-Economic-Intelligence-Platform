"""Great Expectations suite for the World Bank inflation Silver dataset (Day 2)."""
from __future__ import annotations

import great_expectations as gx
from great_expectations import expectations as gxe

COLUMNS = [
    "country_iso3",
    "country_name",
    "indicator_id",
    "year",
    "inflation_pct",
    "inflation_trend",
    "logical_date",
]


def build_suite() -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="world_bank_inflation_silver")

    # Schema
    suite.add_expectation(gxe.ExpectTableColumnsToMatchSet(column_set=COLUMNS))

    # Nulls - identifying fields only. inflation_pct/inflation_trend are
    # legitimately null (not-yet-reported year / no prior year to compare).
    for column in ["country_iso3", "country_name", "indicator_id", "year", "logical_date"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    # Duplicates: one row per (country, indicator, year).
    suite.add_expectation(
        gxe.ExpectCompoundColumnsToBeUnique(column_list=["country_iso3", "indicator_id", "year"])
    )

    # Ranges. Unlike GDP, inflation can legitimately be negative (deflation),
    # so this only catches implausible outliers, not a zero floor.
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="year", min_value=1960, max_value=2100)
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="inflation_pct", min_value=-50, max_value=1000)
    )

    return suite
