"""
Day 1, Step 10 - CLI entrypoint to load a Silver Parquet dataset into the
DuckDB star schema.

Run after a Spark ETL job (Step 8) and its validation (Step 9), e.g.:
    python -m pipelines.warehouse.load_warehouse \
        --source exchange_rate --path /opt/warehouse/silver/exchange_rate

By default it writes to the shared warehouse (`shared_settings.duckdb_path`);
pass `--duckdb-path` to target another file (or `:memory:`).

`--validate` runs the Step 9 Great Expectations suite as a hard gate first, so
this same command can be the "validate then load" step in an Airflow DAG. It is
opt-in rather than automatic: wiring validation into the DAGs as a standing gate
is its own milestone (the schema could still change on Day 2), and this keeps
the loader usable on its own until then.
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

from pipelines.warehouse.loader import LOADERS, WarehouseLoader
from pipelines.warehouse.schema import connect, create_schema


def read_silver(path: str) -> pd.DataFrame:
    """Reads a Silver Parquet dataset from either a local path or MinIO
    (`s3://` / `s3a://`).

    Plain `pd.read_parquet("s3://...")` fails against MinIO with
    ACCESS_DENIED - pyarrow's S3 support defaults to real AWS S3 and needs an
    explicit endpoint override to talk to a non-AWS S3-compatible store, so
    this builds that filesystem by hand from the same env vars the rest of
    the stack already uses for MinIO (`MLFLOW_S3_ENDPOINT_URL`, falling back
    to `MINIO_ENDPOINT`).
    """
    if not path.startswith(("s3://", "s3a://")):
        return pd.read_parquet(path)

    import pyarrow.fs as pafs

    endpoint = os.environ.get("MLFLOW_S3_ENDPOINT_URL") or os.environ.get("MINIO_ENDPOINT", "")
    scheme, _, host = endpoint.partition("://")
    fs = pafs.S3FileSystem(endpoint_override=host or endpoint, scheme=scheme or "http")
    _, _, key = path.partition("://")
    return pd.read_parquet(key, filesystem=fs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=sorted(LOADERS))
    parser.add_argument(
        "--path", required=True, help="Path to the Silver Parquet dataset (local or s3a://...)"
    )
    parser.add_argument(
        "--duckdb-path",
        default=None,
        help="Warehouse file to load into (default: shared_settings.duckdb_path)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run the Step 9 Great Expectations suite as a gate before loading",
    )
    args = parser.parse_args()

    df = read_silver(args.path)

    if args.validate:
        # Imported lazily so the loader has no hard dependency on Great
        # Expectations when the caller has already validated upstream.
        from pipelines.validation.runner import ValidationFailedError, validate_and_raise
        from pipelines.validation.suites import SUITE_BUILDERS

        try:
            validate_and_raise(df, SUITE_BUILDERS[args.source], asset_name=args.source)
        except ValidationFailedError as exc:
            print(f"REFUSING TO LOAD {args.source}: {exc}", file=sys.stderr)
            sys.exit(1)

    con = connect(args.duckdb_path)
    try:
        create_schema(con)
        WarehouseLoader(con).load(args.source, df)
    finally:
        con.close()

    print(f"LOADED {len(df)} silver rows for {args.source} into the warehouse")


if __name__ == "__main__":
    main()
