"""
Day 1, Step 8 - Exchange rate ETL entrypoint: Bronze -> Silver.

Run inside the Spark container, e.g.:
    spark-submit /opt/spark-jobs/etl_exchange_rate.py \
        --bronze-path s3a://bronze/exchange_rate/*/exchange_rate.json \
        --silver-path s3a://silver/exchange_rate
"""
from __future__ import annotations

import argparse

from common import build_spark_session, read_bronze_documents, write_silver
from transforms.exchange_rate import transform


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bronze-path", required=True)
    parser.add_argument("--silver-path", required=True)
    args = parser.parse_args()

    spark = build_spark_session("etl_exchange_rate")
    try:
        bronze_df = read_bronze_documents(spark, args.bronze_path)
        silver_df = transform(bronze_df)
        write_silver(silver_df, args.silver_path, partition_cols=["logical_date"])
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
