"""Day 1, Step 5 - World Bank GDP ingestion. Logic lives in _ingestion_dag_factory.py."""
from _ingestion_dag_factory import build_ingestion_dag

dag = build_ingestion_dag("world_bank")
