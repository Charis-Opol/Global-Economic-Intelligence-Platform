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
    return _paginated(con, "view_gdp", clauses, params, "country_iso3, year", limit, offset)


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
    return _paginated(con, "view_inflation", clauses, params, "country_iso3, year", limit, offset)


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
        con, "view_exchange_rate", clauses, params, "date, base_code, currency", limit, offset
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
    return _paginated(con, "view_weather", clauses, params, "date, latitude, longitude", limit, offset)


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
    return _paginated(con, "view_crypto", clauses, params, "date, coin_id", limit, offset)


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
