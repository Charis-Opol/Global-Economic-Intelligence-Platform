"""
Day 2 - World Bank inflation ETL entrypoint: Bronze -> Silver.

Run inside the Spark container, e.g.:
    spark-submit /opt/spark-jobs/etl_world_bank_inflation.py \
        --bronze-path s3a://bronze/world_bank_inflation/*/world_bank_inflation.json \
        --silver-path s3a://silver/world_bank_inflation
"""
from __future__ import annotations

import argparse

from common import build_spark_session, read_bronze_documents, write_silver
from transforms.world_bank_inflation import transform


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bronze-path", required=True)
    parser.add_argument("--silver-path", required=True)
    args = parser.parse_args()

    spark = build_spark_session("etl_world_bank_inflation")
    try:
        bronze_df = read_bronze_documents(spark, args.bronze_path)
        silver_df = transform(bronze_df)
        write_silver(silver_df, args.silver_path, partition_cols=["year"])
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
