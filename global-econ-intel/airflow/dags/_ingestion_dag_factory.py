"""
Factory for the six near-identical ingestion DAGs (Day 1, Step 5; extended
to the full Bronze -> Silver -> warehouse chain after Day 3 wrap-up).

Each DAG only differs by source name, so the DAG-building logic lives
here once. Files like `ingest_world_bank.py` just call
`build_ingestion_dag(...)` - this keeps every DAG file thin and easy to
diff, instead of six copies of the same schedule/retry boilerplate.

Note the leading underscore: Airflow scans every .py file in `dags/` but
only registers objects that are actual DAG instances. This file defines
none at module level, so Airflow parses it harmlessly and moves on.

Originally this only ran the Bronze ingestion task - the Spark ETL
(Bronze -> Silver) and warehouse load (Silver -> DuckDB) were separate
manual/CLI steps. That meant fresh ingestion never actually reached the
app: the backend and Superset only ever read the DuckDB warehouse, which
sat frozen at whatever was last loaded by hand. Chaining all three tasks
here means a single daily DAG run keeps the whole thing current with zero
manual steps.
"""
from __future__ import annotations

import sys
from datetime import timedelta
from importlib import import_module

import pendulum
from airflow import DAG
from airflow.decorators import task

from pipelines.tasks.ingestion import run_ingestion

DEFAULT_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

# Matches each spark/jobs/etl_<source>.py's own write_silver(partition_cols=):
# World Bank sources are annual-history data partitioned by year; every other
# source is a daily snapshot partitioned by logical_date.
_YEAR_PARTITIONED = {"world_bank", "world_bank_inflation"}

# Same path spark-master/spark-worker mount spark/jobs at - see
# docker-compose.yml's airflow-common volumes.
_SPARK_JOBS_DIR = "/opt/spark-jobs"

_SPARK_MASTER_URL = "spark://spark-master:7077"


def _run_spark_etl(source_name: str) -> None:
    """Runs the Bronze -> Silver transform for `source_name` in-process.

    Reuses spark/jobs/common.py and spark/jobs/transforms/<source>.py
    directly (mounted read-only at /opt/spark-jobs) rather than shelling out
    to spark-submit - this Celery worker process already has its own JVM
    (openjdk, installed for exactly this) and pyspark pinned to match the
    cluster's Spark version, so an in-process SparkSession connecting to
    spark://spark-master:7077 works the same way spark-submit's client mode
    does, without needing to locate that script on PATH.
    """
    if _SPARK_JOBS_DIR not in sys.path:
        sys.path.insert(0, _SPARK_JOBS_DIR)

    from common import build_spark_session, read_bronze_documents, write_silver  # noqa: E402

    transform = import_module(f"transforms.{source_name}").transform
    partition_cols = ["year"] if source_name in _YEAR_PARTITIONED else ["logical_date"]

    spark = build_spark_session(f"etl_{source_name}", master=_SPARK_MASTER_URL)
    try:
        bronze_df = read_bronze_documents(spark, f"s3a://bronze/{source_name}/*/{source_name}.json")
        silver_df = transform(bronze_df)
        write_silver(silver_df, f"s3a://silver/{source_name}", partition_cols=partition_cols)
    finally:
        spark.stop()


def _load_to_warehouse(source_name: str) -> None:
    """Loads the just-written Silver dataset into the DuckDB warehouse -
    the same `WarehouseLoader` the CLI (`pipelines.warehouse.load_warehouse`)
    uses, called directly here instead of via subprocess.
    """
    from pipelines.warehouse.loader import WarehouseLoader
    from pipelines.warehouse.load_warehouse import read_silver
    from pipelines.warehouse.schema import connect, create_schema

    df = read_silver(f"s3a://silver/{source_name}")
    con = connect()
    try:
        create_schema(con)
        WarehouseLoader(con).load(source_name, df)
    finally:
        con.close()


def build_ingestion_dag(source_name: str) -> DAG:
    with DAG(
        dag_id=f"ingest_{source_name}",
        description=(
            f"Fetch {source_name} data, land it in Bronze, transform it to "
            "Silver, and load it into the warehouse."
        ),
        schedule="@daily",
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        default_args=DEFAULT_ARGS,
        tags=["ingestion", "bronze", source_name],
    ) as dag:

        @task(task_id="fetch_and_save_to_bronze")
        def fetch_and_save(logical_date=None):
            return run_ingestion(source_name, logical_date=logical_date)

        @task(task_id="run_spark_etl")
        def run_spark_etl(_bronze_result=None) -> None:
            _run_spark_etl(source_name)

        @task(task_id="load_warehouse")
        def load_warehouse(_etl_result=None) -> None:
            _load_to_warehouse(source_name)

        load_warehouse(run_spark_etl(fetch_and_save()))

    return dag
