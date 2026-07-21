FROM apache/superset:latest

USER root
# duckdb pinned to match the version that actually writes warehouse.duckdb
# (pipelines/warehouse) - DuckDB's file format isn't always readable across
# versions, so these two must stay in lockstep.
RUN pip install --no-cache-dir duckdb==1.5.4 duckdb-engine==0.17.0

# Already on the base image's PYTHONPATH - Superset auto-loads
# superset_config.py from here, no SUPERSET_CONFIG_PATH env var needed.
COPY superset_config.py /app/pythonpath/superset_config.py

USER superset
