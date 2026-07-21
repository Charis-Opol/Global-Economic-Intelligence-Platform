"""
DuckDB access layer (Day 2, Step 6).

The backend never writes to the warehouse - it only reads what
`pipelines.warehouse` (Day 1, Step 10) already loaded there. Every request
opens its own short-lived read-only connection rather than sharing one
pooled connection, so the backend never contends for the file lock a
concurrent warehouse load might be holding.
"""
from __future__ import annotations

from typing import Any, Iterator

import duckdb
from fastapi import HTTPException

from app.core.config import settings


def get_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    try:
        con = duckdb.connect(settings.duckdb_path, read_only=True)
    except duckdb.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Warehouse is not available yet. Has it been loaded? "
                "(pipelines.warehouse.load_warehouse)"
            ),
        ) from exc
    try:
        yield con
    finally:
        con.close()


def fetch_rows(con: duckdb.DuckDBPyConnection, sql: str, params: list[Any]) -> list[dict[str, Any]]:
    """Runs `sql` and returns rows as plain dicts, keyed by cursor column name.

    Kept dependency-free (no pandas) - the backend's own requirements.txt
    doesn't otherwise need it, and `pipelines/` already owns that dependency
    for the loader side.
    """
    cursor = con.execute(sql, params)
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_scalar(con: duckdb.DuckDBPyConnection, sql: str, params: list[Any]) -> Any:
    return con.execute(sql, params).fetchone()[0]


def where_clause(clauses: list[str]) -> str:
    """Joins pre-built (column-side-fixed, value-parameterized) clauses.

    Callers only ever append hardcoded column comparisons like
    `"country_iso3 = ?"` here - user-supplied values always travel as bound
    `?` parameters, never interpolated into the SQL text, so this stays safe
    against injection regardless of what a caller passes as a filter value.
    """
    return f"WHERE {' AND '.join(clauses)}" if clauses else ""
