"""Great Expectations suite for the World Bank Silver dataset (Day 1, Step 9)."""
from __future__ import annotations

import great_expectations as gx
from great_expectations import expectations as gxe

COLUMNS = [
    "country_iso3",
    "country_name",
    "indicator_id",
    "year",
    "gdp_usd",
    "gdp_growth_rate",
    "logical_date",
]


def build_suite() -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="world_bank_silver")

    # Schema
    suite.add_expectation(gxe.ExpectTableColumnsToMatchSet(column_set=COLUMNS))

    # Nulls - identifying fields only. gdp_usd and gdp_growth_rate are
    # legitimately null (not-yet-reported year / no prior year to compare).
    for column in ["country_iso3", "country_name", "indicator_id", "year", "logical_date"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    # Duplicates: one row per (country, indicator, year).
    suite.add_expectation(
        gxe.ExpectCompoundColumnsToBeUnique(column_list=["country_iso3", "indicator_id", "year"])
    )

    # Ranges
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="year", min_value=1960, max_value=2100)
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="gdp_usd", min_value=0, max_value=None)
    )

    return suite
