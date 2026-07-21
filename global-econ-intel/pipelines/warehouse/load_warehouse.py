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
import sys

import pandas as pd

from pipelines.warehouse.loader import LOADERS, WarehouseLoader
from pipelines.warehouse.schema import connect, create_schema


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=sorted(LOADERS))
    parser.add_argument("--path", required=True, help="Path to the Silver Parquet dataset")
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

    df = pd.read_parquet(args.path)

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
