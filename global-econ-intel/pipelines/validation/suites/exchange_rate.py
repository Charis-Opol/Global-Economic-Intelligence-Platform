"""Great Expectations suite for the Exchange Rate Silver dataset (Day 1, Step 9)."""
from __future__ import annotations

import great_expectations as gx
from great_expectations import expectations as gxe

COLUMNS = ["base_code", "currency", "rate", "exchange_momentum", "logical_date"]


def build_suite() -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="exchange_rate_silver")

    suite.add_expectation(gxe.ExpectTableColumnsToMatchSet(column_set=COLUMNS))

    for column in ["base_code", "currency", "rate", "logical_date"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    # Duplicates: one row per (base currency, quote currency, day).
    suite.add_expectation(
        gxe.ExpectCompoundColumnsToBeUnique(column_list=["base_code", "currency", "logical_date"])
    )

    # Ranges: a rate of zero or below is never valid.
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="rate", min_value=0, strict_min=True, max_value=None)
    )

    return suite
