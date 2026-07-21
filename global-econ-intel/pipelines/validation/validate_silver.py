"""
Day 1, Step 9 - CLI entrypoint to validate a Silver Parquet dataset.

Run after a Spark ETL job (Step 8), e.g.:
    python -m pipelines.validation.validate_silver \
        --source exchange_rate --path /opt/warehouse/silver/exchange_rate

Silver datasets here are small (one source, one partition at a time),
so this reads with pandas rather than spinning up Spark again just to
validate - Great Expectations' pandas backend is also the most mature
and stable of its execution engines.
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites import SUITE_BUILDERS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=sorted(SUITE_BUILDERS))
    parser.add_argument("--path", required=True, help="Path to the Silver Parquet dataset")
    args = parser.parse_args()

    df = pd.read_parquet(args.path)
    outcome = validate_dataframe(df, SUITE_BUILDERS[args.source], asset_name=args.source)

    if not outcome.success:
        print(f"VALIDATION FAILED for {args.source}: {outcome.failed_expectations}", file=sys.stderr)
        sys.exit(1)

    print(f"VALIDATION PASSED for {args.source} ({outcome.total_expectations} expectations)")


if __name__ == "__main__":
    main()
