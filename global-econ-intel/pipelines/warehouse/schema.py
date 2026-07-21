"""
Warehouse connection + schema management (Day 1, Step 10; views added Day 2, Step 1).

The canonical DDL lives in `warehouse/schema/*.sql` so it is a single source
of truth shared with Superset and the Day 2 backend, rather than being buried
in a Python string literal. This module reads those files and applies them to
a DuckDB connection.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from config.settings import shared_settings

# pipelines/warehouse/schema.py -> repo root is two parents up.
_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "warehouse" / "schema"
# star_schema.sql must apply first - views.sql selects from the tables it creates.
_DDL_FILES = ["star_schema.sql", "views.sql"]


def connect(db_path: str | None = None, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection.

    Defaults to the shared warehouse path (`shared_settings.duckdb_path`).
    Pass `":memory:"` for an ephemeral database - what the tests use, the same
    way the Step 9 validation runner uses an ephemeral Great Expectations
    context.
    """
    return duckdb.connect(db_path or shared_settings.duckdb_path, read_only=read_only)


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Apply the star-schema DDL and repository views. Idempotent - safe to
    call before every load.

    Each file is parsed by DuckDB in one call, which handles `--` comments and
    the multiple statements itself (splitting on `;` in Python would wrongly
    break on semicolons that appear inside comments).
    """
    for filename in _DDL_FILES:
        con.execute((_SCHEMA_DIR / filename).read_text(encoding="utf-8"))
