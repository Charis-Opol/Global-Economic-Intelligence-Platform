"""Day 1, Step 5 - Open-Meteo weather ingestion. Logic lives in _ingestion_dag_factory.py."""
from _ingestion_dag_factory import build_ingestion_dag

dag = build_ingestion_dag("open_meteo")
