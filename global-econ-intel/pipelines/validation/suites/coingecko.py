"""Great Expectations suite for the CoinGecko Silver dataset (Day 1, Step 9)."""
from __future__ import annotations

import great_expectations as gx
from great_expectations import expectations as gxe

COLUMNS = [
    "coin_id",
    "symbol",
    "name",
    "price_usd",
    "market_cap_usd",
    "volume_usd",
    "price_change_pct_24h",
    "volatility_7d",
    "logical_date",
]


def build_suite() -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="coingecko_silver")

    suite.add_expectation(gxe.ExpectTableColumnsToMatchSet(column_set=COLUMNS))

    for column in ["coin_id", "price_usd", "logical_date"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    # Duplicates: one row per (coin, day).
    suite.add_expectation(gxe.ExpectCompoundColumnsToBeUnique(column_list=["coin_id", "logical_date"]))

    # Ranges
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="price_usd", min_value=0, max_value=None)
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="market_cap_usd", min_value=0, max_value=None)
    )
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="volume_usd", min_value=0, max_value=None)
    )

    return suite
