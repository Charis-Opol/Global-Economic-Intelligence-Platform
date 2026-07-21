"""
Stored-query repository layer for the ML side (Day 2, Step 1/4).

Thin wrappers around the same `view_*` views the backend queries (see
`warehouse/schema/views.sql` and `backend/app/repository.py`) - both sides
read identical numbers for identical rows because both query the same views,
not because the logic is duplicated between them. This side just returns
whole pandas DataFrames (training wants the full feature set), where the
backend side returns filtered/paginated dict pages (the API wants a slice).
"""
from __future__ import annotations

import duckdb
import pandas as pd


def get_gdp_features(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM view_gdp ORDER BY country_iso3, year").df()


def get_inflation_features(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM view_inflation ORDER BY country_iso3, year").df()


def get_exchange_rate_features(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(
        "SELECT * FROM view_exchange_rate ORDER BY base_code, currency, date"
    ).df()


def get_crypto_features(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM view_crypto ORDER BY coin_id, date").df()
