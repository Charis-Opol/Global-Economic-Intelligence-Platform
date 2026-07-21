"""
Warehouse connection + schema management (Day 1, Step 10).

The canonical DDL lives in `warehouse/schema/star_schema.sql` so it is a
single source of truth shared with Superset and the Day 2 backend, rather than
being buried in a Python string literal. This module reads that file and
applies it to a DuckDB connection.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from config.settings import shared_settings

# pipelines/warehouse/schema.py -> repo root is two parents up.
_DDL_PATH = Path(__file__).resolve().parents[2] / "warehouse" / "schema" / "star_schema.sql"


def connect(db_path: str | None = None, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection.

    Defaults to the shared warehouse path (`shared_settings.duckdb_path`).
    Pass `":memory:"` for an ephemeral database - what the tests use, the same
    way the Step 9 validation runner uses an ephemeral Great Expectations
    context.
    """
    return duckdb.connect(db_path or shared_settings.duckdb_path, read_only=read_only)


def _read_ddl() -> str:
    return _DDL_PATH.read_text(encoding="utf-8")


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Apply the star-schema DDL. Idempotent - safe to call before every load.

    Statements are executed one at a time so this works identically across
    DuckDB versions regardless of whether the driver runs multi-statement
    strings. The DDL contains no semicolons inside string literals, so a plain
    split on ``;`` is safe.
    """
    for statement in _read_ddl().split(";"):
        if statement.strip():
            con.execute(statement)
