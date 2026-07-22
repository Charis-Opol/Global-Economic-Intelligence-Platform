"""
Shared Spark session builder and I/O helpers for Day 1, Step 8 ETL jobs.

Transformation logic itself lives in transforms/ as pure DataFrame ->
DataFrame functions, kept deliberately separate from I/O so it can be
unit tested with a local Spark session and no dependency on MinIO or
the Airflow container.
"""
from __future__ import annotations

import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def build_spark_session(app_name: str, master: str | None = None) -> SparkSession:
    """`master` is only needed for in-process callers (the Airflow ingestion
    DAGs' own run_spark_etl task) - spark-submit's own `--master` flag
    already sets `spark.master` before this even runs, so the CLI jobs never
    need to pass it.
    """
    builder = SparkSession.builder.appName(app_name).config(
        # Only overwrite the specific partitions a job actually writes,
        # so a rerun for one day never wipes out other days already in Silver.
        "spark.sql.sources.partitionOverwriteMode",
        "dynamic",
    )
    if master:
        builder = builder.master(master)

    minio_endpoint = os.environ.get("MINIO_ENDPOINT")
    if minio_endpoint:
        builder = (
            builder.config("spark.hadoop.fs.s3a.endpoint", minio_endpoint)
            .config("spark.hadoop.fs.s3a.access.key", os.environ.get("MINIO_ROOT_USER", ""))
            .config("spark.hadoop.fs.s3a.secret.key", os.environ.get("MINIO_ROOT_PASSWORD", ""))
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        )

    return builder.getOrCreate()


def read_bronze_documents(spark: SparkSession, path: str) -> DataFrame:
    """
    Reads one or more bronze JSON documents (glob-friendly, e.g.
    `s3a://bronze/exchange_rate/*/exchange_rate.json`) and normalizes
    `logical_date` from an ISO-8601 timestamp string down to a plain date,
    since every transform partitions or dedupes on it.
    """
    raw = spark.read.option("multiLine", True).json(path)
    return raw.withColumn(
        "logical_date", F.substring(F.col("logical_date"), 1, 10).cast("date")
    )


def write_silver(df: DataFrame, path: str, partition_cols: list[str]) -> None:
    """Writes Silver Parquet, overwriting only the touched partitions."""
    df.write.mode("overwrite").partitionBy(*partition_cols).parquet(path)
