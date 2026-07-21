"""
Factory for the five near-identical ingestion DAGs (Day 1, Step 5).

Each DAG only differs by source name, so the DAG-building logic lives
here once. Files like `ingest_world_bank.py` just call
`build_ingestion_dag(...)` - this keeps every DAG file thin and easy to
diff, instead of five copies of the same schedule/retry boilerplate.

Note the leading underscore: Airflow scans every .py file in `dags/` but
only registers objects that are actual DAG instances. This file defines
none at module level, so Airflow parses it harmlessly and moves on.
"""
from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.decorators import task

from pipelines.tasks.ingestion import run_ingestion

DEFAULT_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


def build_ingestion_dag(source_name: str) -> DAG:
    with DAG(
        dag_id=f"ingest_{source_name}",
        description=f"Fetch {source_name} data and write it to the Bronze bucket.",
        schedule="@daily",
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        default_args=DEFAULT_ARGS,
        tags=["ingestion", "bronze", source_name],
    ) as dag:

        @task(task_id="fetch_and_save_to_bronze")
        def fetch_and_save(logical_date=None):
            return run_ingestion(source_name, logical_date=logical_date)

        fetch_and_save()

    return dag
