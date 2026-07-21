"""Day 2 - World Bank inflation ingestion. Logic lives in _ingestion_dag_factory.py."""
from _ingestion_dag_factory import build_ingestion_dag

dag = build_ingestion_dag("world_bank_inflation")
