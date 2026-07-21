# Global Economic Intelligence Platform

A data platform that ingests economic, weather, crypto, and news data,
transforms it through a medallion (Bronze/Silver/Gold) architecture, and
exposes it via API, dashboards, and ML forecasts.

This repository is being built as a series of small, testable milestones
rather than one large generation pass. See `docs/ARCHITECTURE.md` for the
current system diagram and `docs/ROADMAP.md`-equivalent (the 3-Day Sprint
plan) for what's built vs. what's next.

## Current status: Day 1, Step 8 — PySpark ETL (Bronze → Silver)

Completed so far:
- **Step 1**: `docker-compose.yml`, folder structure, `.env.example`,
  placeholder Dockerfiles for services with no logic yet
- **Step 4**: `pipelines/connectors/` — five source connectors with
  retries, structured logging, validation, and pagination
- **Step 5**: `airflow/dags/` — one ingestion DAG per source, writing
  idempotently to the Bronze bucket
- **Step 8**: `spark/jobs/` — one ETL job per source
  (`etl_world_bank.py`, `etl_open_meteo.py`, `etl_exchange_rate.py`,
  `etl_coingecko.py`, `etl_newsapi.py`), each reading Bronze JSON,
  cleaning, normalizing nested/array/map structures into flat rows,
  merging (deduping) across overlapping ingestion runs, engineering one
  feature per source (GDP YoY growth, rainfall anomaly, exchange
  momentum, 7-day crypto volatility, daily article volume), and writing
  partitioned Silver Parquet. 16 new tests run against a **real local
  Spark session** (not mocked) — 35 tests total, all passing.

What does **not** exist yet (intentionally — separate milestones):
- Great Expectations validation suites (Step 9)
- DuckDB star schema (Step 10)
- ML pipelines / FastAPI domain endpoints (Day 2)
- React application UI (Day 3)
- Superset dashboards (Day 3)

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

All 35 tests run offline. Connectors mock HTTP, ingestion/storage tests
mock boto3, and the Spark transform tests spin up a real local (JVM)
Spark session with small in-memory datasets — no live API keys, MinIO,
or a running Airflow/Spark cluster required to verify the logic itself.
Requires a JDK (11+) on your machine for the Spark tests to run.

## Getting started

```bash
cp .env.example .env
# edit .env with real secrets (Fernet key, passwords, Superset secret key)

docker compose up -d --build
```

Then verify:

| Service            | URL                          |
|--------------------|------------------------------|
| Airflow             | http://localhost:8080        |
| MinIO Console       | http://localhost:9001         |
| MLflow              | http://localhost:5000         |
| Superset            | http://localhost:8088         |
| Spark Master UI     | http://localhost:8081         |
| Backend health check| http://localhost:8000/health  |
| Frontend            | http://localhost:5173         |

## Acceptance criteria for this milestone

- [ ] `docker compose up -d --build` succeeds with no errors
- [ ] All containers report healthy / running (`docker compose ps`)
- [ ] Airflow UI is reachable and login works with `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`
- [ ] MinIO console shows `bronze`, `silver`, `gold` buckets already created
- [ ] `GET http://localhost:8000/health` returns `{"status": "ok", ...}`

Once all of the above are true, this milestone is done.

### Acceptance criteria for Step 4 (connectors)

- [ ] `pytest tests/test_connectors/ -v` passes (14/14)
- [ ] Each connector raises `ConnectorRequestError` (not a raw `requests`
      exception) after exhausting retries
- [ ] Each connector raises `ConnectorValidationError` on malformed data
- [ ] `NewsAPIConnector` fails fast with a clear error when `NEWSAPI_KEY`
      is unset, without making a network call

### Acceptance criteria for Step 5 (Airflow DAGs)

- [ ] `pytest tests/test_pipelines/ -v` passes (5/5)
- [ ] `docker compose up -d --build` succeeds and `airflow dags list`
      shows all five `ingest_*` DAGs with no import errors
- [ ] Manually triggering `ingest_exchange_rate` (no API key required)
      completes successfully and a JSON object appears at
      `bronze/exchange_rate/<date>/exchange_rate.json` in the MinIO console
- [ ] Triggering the same DAG a second time for the same day overwrites
      that object rather than creating a second one

### Acceptance criteria for Step 8 (PySpark ETL)

- [ ] `pytest tests/test_spark/ -v` passes (16/16) using a real local
      Spark session
- [ ] Each transform drops genuinely invalid rows (missing country code,
      zero/negative exchange rate, missing article title/URL) while
      keeping legitimately-null business values (e.g. unreported GDP)
- [ ] Rerunning ingestion for a day that overlaps a previous run
      (verified for World Bank revisions, Open-Meteo's rolling window,
      CoinGecko, and NewsAPI) produces one row per natural key, not a
      duplicate
- [ ] Inside the Spark container: `spark-submit /opt/spark-jobs/etl_exchange_rate.py --bronze-path s3a://bronze/exchange_rate/*/exchange_rate.json --silver-path s3a://silver/exchange_rate`
      completes and Parquet files appear under `silver/exchange_rate/` in MinIO

Next milestone: Day 1, Step 9 — Great Expectations validation suites
(nulls, duplicates, ranges, schema) run against the Silver layer these
jobs produce.

## Repository layout

```
backend/       FastAPI service (domain endpoints added Day 2)
frontend/      React app (full UI added Day 3)
airflow/       DAGs (one per source), plugins, custom Airflow image
spark/         jobs/ (one ETL entrypoint per source, transforms/ holding
               the pure clean/normalize/merge/feature-engineer logic),
               custom Spark image
warehouse/     DuckDB file + star schema DDL
data/          Local mirror of bronze/silver/gold (MinIO is source of truth)
models/        Trained model artifacts (MLflow registry is source of truth)
pipelines/     connectors/ (World Bank, Open-Meteo, ExchangeRate, CoinGecko,
               NewsAPI), storage/ (MinIO Bronze writer), tasks/ (shared
               ingestion logic imported by DAGs)
config/        Shared Pydantic settings used across services
tests/         Cross-service integration tests
docs/          Architecture and planning docs
scripts/       One-off ops scripts (e.g. Postgres multi-db init)
```
