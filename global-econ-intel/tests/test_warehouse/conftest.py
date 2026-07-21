from __future__ import annotations

import pytest

from pipelines.warehouse.loader import WarehouseLoader
from pipelines.warehouse.schema import connect, create_schema


@pytest.fixture
def loader():
    """A WarehouseLoader over a fresh in-memory star schema.

    The DuckDB analogue of the Step 9 ephemeral Great Expectations context:
    no warehouse file on disk, no MinIO, no Spark - just the DDL applied to an
    in-memory database, so every test starts from an empty, real star schema.
    """
    con = connect(":memory:")
    create_schema(con)
    try:
        yield WarehouseLoader(con)
    finally:
        con.close()
