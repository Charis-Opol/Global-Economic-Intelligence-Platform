"""
Stored-query repository layer (Day 2, Step 1).

Routers call these functions instead of building SQL inline - every function
here is a thin, filtered/paginated wrapper around one of the warehouse's
`view_*` views (see `warehouse/schema/views.sql`), so the WHERE-building and
pagination logic that used to live duplicated across each router lives here
once. Views already resolve surrogate keys to human-readable names and carry
the lag/rolling-average feature columns, so nothing here does its own JOINs.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import duckdb

from app.db import fetch_rows, fetch_scalar, where_clause


def _paginated(
    con: duckdb.DuckDBPyConnection,
    source: str,
    clauses: list[str],
    params: list[Any],
    order_by: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    where = where_clause(clauses)
    total = fetch_scalar(con, f"SELECT count(*) FROM {source} {where}", params)
    rows = fetch_rows(
        con,
        f"SELECT * FROM {source} {where} ORDER BY {order_by} LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


def list_countries(
    con: duckdb.DuckDBPyConnection, *, search: str | None = None, limit: int = 50, offset: int = 0
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []
    if search:
        clauses.append("(country_iso3 ILIKE ? OR country_name ILIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    return _paginated(con, "dim_country", clauses, params, "country_iso3", limit, offset)


def list_gdp(
    con: duckdb.DuckDBPyConnection,
    *,
    country: str | None = None,
    indicator_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses, params = [], []
    if country:
        clauses.append("country_iso3 = ?")
        params.append(country.upper())
    if indicator_id:
        clauses.append("indicator_id = ?")
        params.append(indicator_id)
    if year_min is not None:
        clauses.append("year >= ?")
        params.append(year_min)
    if year_max is not None:
        clauses.append("year <= ?")
        params.append(year_max)
    # Most recent year first by default - without an explicit sort, this
    # otherwise starts at 1960 (ascending country_iso3, year), which reads as
    # stale data on a page whose whole point is current economic figures.
    return _paginated(con, "view_gdp", clauses, params, "year DESC, country_iso3", limit, offset)


def list_inflation(
    con: duckdb.DuckDBPyConnection,
    *,
    country: str | None = None,
    indicator_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses, params = [], []
    if country:
        clauses.append("country_iso3 = ?")
        params.append(country.upper())
    if indicator_id:
        clauses.append("indicator_id = ?")
        params.append(indicator_id)
    if year_min is not None:
        clauses.append("year >= ?")
        params.append(year_min)
    if year_max is not None:
        clauses.append("year <= ?")
        params.append(year_max)
    return _paginated(con, "view_inflation", clauses, params, "year DESC, country_iso3", limit, offset)


def list_exchange_rates(
    con: duckdb.DuckDBPyConnection,
    *,
    base: str | None = None,
    quote: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses, params = [], []
    if base:
        clauses.append("base_code = ?")
        params.append(base.upper())
    if quote:
        clauses.append("currency = ?")
        params.append(quote.upper())
    if date_from:
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        params.append(date_to)
    return _paginated(
        con, "view_exchange_rate", clauses, params, "date DESC, base_code, currency", limit, offset
    )


def list_weather(
    con: duckdb.DuckDBPyConnection,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses, params = [], []
    if latitude is not None:
        clauses.append("latitude = ?")
        params.append(latitude)
    if longitude is not None:
        clauses.append("longitude = ?")
        params.append(longitude)
    if date_from:
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        params.append(date_to)
    return _paginated(con, "view_weather", clauses, params, "date DESC, latitude, longitude", limit, offset)


def list_crypto(
    con: duckdb.DuckDBPyConnection,
    *,
    coin_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses, params = [], []
    if coin_id:
        clauses.append("coin_id = ?")
        params.append(coin_id.lower())
    if date_from:
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        params.append(date_to)
    return _paginated(con, "view_crypto", clauses, params, "date DESC, coin_id", limit, offset)


def latest_gdp_row(con: duckdb.DuckDBPyConnection, country: str) -> dict[str, Any] | None:
    """Most recent row for `country` from view_gdp - the feature row
    /predictions feeds into the champion GDP model."""
    rows = fetch_rows(
        con, "SELECT * FROM view_gdp WHERE country_iso3 = ? ORDER BY year DESC LIMIT 1",
        [country.upper()],
    )
    return rows[0] if rows else None


def latest_inflation_row(con: duckdb.DuckDBPyConnection, country: str) -> dict[str, Any] | None:
    rows = fetch_rows(
        con, "SELECT * FROM view_inflation WHERE country_iso3 = ? ORDER BY year DESC LIMIT 1",
        [country.upper()],
    )
    return rows[0] if rows else None


def latest_exchange_rate_row(
    con: duckdb.DuckDBPyConnection, base: str, quote: str
) -> dict[str, Any] | None:
    rows = fetch_rows(
        con,
        "SELECT * FROM view_exchange_rate WHERE base_code = ? AND currency = ? "
        "ORDER BY date DESC LIMIT 1",
        [base.upper(), quote.upper()],
    )
    return rows[0] if rows else None


def latest_crypto_row(con: duckdb.DuckDBPyConnection, coin_id: str) -> dict[str, Any] | None:
    rows = fetch_rows(
        con, "SELECT * FROM view_crypto WHERE coin_id = ? ORDER BY date DESC LIMIT 1",
        [coin_id.lower()],
    )
    return rows[0] if rows else None


def list_news(
    con: duckdb.DuckDBPyConnection,
    *,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    clauses, params = [], []
    if source:
        clauses.append("source_name = ?")
        params.append(source)
    if date_from:
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        params.append(date_to)
    if q:
        clauses.append("title ILIKE ?")
        params.append(f"%{q}%")
    return _paginated(con, "view_news", clauses, params, "date DESC, url", limit, offset)
