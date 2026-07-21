"""
DuckDB star-schema warehouse (Day 1, Step 10).

Loads validated Silver datasets into a star schema (conformed date dimension,
one dimension per entity, one fact per source). Mirrors the shape of the
`pipelines.validation` package: pure, DataFrame-in logic that unit tests can
drive against an in-memory DuckDB with no MinIO or Spark required.
"""
from pipelines.warehouse.loader import LOADERS, WarehouseLoader
from pipelines.warehouse.schema import connect, create_schema

__all__ = ["LOADERS", "WarehouseLoader", "connect", "create_schema"]
