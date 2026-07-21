# Global Economic Intelligence Platform

A data platform that ingests economic, weather, crypto, and news data,
transforms it through a medallion (Bronze/Silver/Gold) architecture, and
exposes it via API, dashboards, and ML forecasts.

This repository is being built as a series of small, testable milestones
rather than one large generation pass. See `docs/ARCHITECTURE.md` for the
current system diagram and `docs/ROADMAP.md`-equivalent (the 3-Day Sprint
plan) for what's built vs. what's next.

## Current status: Day 2, Step 6 — FastAPI domain endpoints

Completed so far:
- **Step 1**: `docker-compose.yml`, folder structure, `.env.example`,
  placeholder Dockerfiles for services with no logic yet
- **Step 4**: `pipelines/connectors/` — five source connectors with
  retries, structured logging, validation, and pagination
- **Step 5**: `airflow/dags/` — one ingestion DAG per source, writing
  idempotently to the Bronze bucket
- **Step 8**: `spark/jobs/` — one ETL job per source: clean, normalize,
  merge (dedupe), engineer one feature, write partitioned Silver Parquet
- **Step 9**: `pipelines/validation/` — one Great Expectations suite
  per Silver dataset, each checking **schema** (expected columns),
  **nulls** (only on fields that should never be missing — legitimately
  optional fields like unreported GDP or a missing news byline are left
  alone), **duplicates** (uniqueness on each dataset's natural key), and
  **ranges** (e.g. rate > 0, latitude ∈ [-90, 90], year ∈ [1960, 2100]).
  10 new tests — each suite gets a "valid data passes" case and a
  "catches every violation type at once" case.
- **Step 10**: `pipelines/warehouse/` — loads the validated Silver layer
  into a **DuckDB star schema** (`warehouse/schema/star_schema.sql`): a
  conformed `dim_date`, one dimension per entity (country, currency,
  coin, location, news source), and one fact per source. Dimensions
  upsert on their natural key onto a stable surrogate key; facts upsert
  on their grain — so a rerun leaves the warehouse identical. 18 new
  tests.
- **Step 6**: `backend/app/routers/` — one read-only FastAPI router per
  warehouse fact: `/countries` + `/gdp`, `/exchange-rates`, `/weather`,
  `/crypto`, `/news`. Each supports simple filters (country/coin/base
  currency, date ranges, a title substring search for news) and a shared
  pagination envelope (`items`, `total`, `limit`, `offset`). The backend
  opens a fresh read-only DuckDB connection per request — no pooled
  writer, no dependency on `pipelines/` at runtime — and returns `503`
  rather than `500` if the warehouse hasn't been loaded yet. 16 new
  tests. 79 tests total, all passing.

What does **not** exist yet (intentionally — separate milestones):
- ML pipelines / MLflow-registered model / `/predictions` endpoint
  (Day 2, Step 7)
- React application UI (Day 3)
- Superset dashboards (Day 3)
- Wiring the validate → load step into the Airflow DAGs as an automatic
  gate after each Spark job. The pieces exist (`validate_silver.py` from
  Step 9, and `load_warehouse.py --validate` from Step 10 already chains
  them), but they aren't wired into a DAG yet — a natural next increment,
  deliberately deferred so it doesn't get thrown away if Day 2's needs
  change the schema.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

All 79 tests run offline. Connectors mock HTTP, ingestion/storage tests
mock boto3, Spark transform tests spin up a real local Spark session,
Great Expectations tests run against an ephemeral (in-memory) context,
warehouse tests load into an in-memory DuckDB, and backend tests drive a
FastAPI `TestClient` against that same in-memory warehouse via a
dependency override — no persistent GX project, warehouse file, or
running server needed. Requires a JDK (11+) on your machine for the
Spark tests.

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

### Acceptance criteria for Step 9 (Great Expectations)

- [ ] `pytest tests/test_validation/ -v` passes (10/10)
- [ ] Each suite's "valid data" case reports `success: True`
- [ ] Each suite's "broken data" case reports `success: False` and the
      failed-expectations list includes the null/duplicate/range check
      that specific broken row should trip
- [ ] `python -m pipelines.validation.validate_silver --source exchange_rate --path <silver parquet path>`
      runs against a real Silver Parquet file (produced by Step 8) and
      prints PASSED or FAILED with a non-zero exit code on failure

### Acceptance criteria for Step 10 (DuckDB star schema)

- [ ] `pytest tests/test_warehouse/ -v` passes (18/18) against an
      in-memory DuckDB
- [ ] `python -m pipelines.warehouse.load_warehouse --source exchange_rate --path <silver parquet path>`
      loads a real Silver Parquet file (produced by Step 8) into
      `warehouse/warehouse.duckdb` and prints how many rows it loaded
- [ ] Loading the same Silver dataset twice leaves row counts unchanged
      (dimensions upsert on natural key, facts upsert on grain)
- [ ] Adding `--validate` runs the Step 9 suite first and refuses to load
      (non-zero exit) when validation fails
- [ ] The loaded warehouse answers a star query, e.g.
      `SELECT c.name, f.price_usd FROM fact_crypto f JOIN dim_coin c USING (coin_key)`

Day 1 is complete: raw data → Bronze → Spark ETL → Silver → validation →
DuckDB warehouse.

### Acceptance criteria for Step 6 (FastAPI domain endpoints)

- [ ] `pytest tests/test_backend/ -v` passes (16/16) against an in-memory
      DuckDB via a `TestClient` + dependency override
- [ ] With a real warehouse loaded (Step 10), `docker compose up -d --build`
      followed by `GET http://localhost:8000/countries` returns the
      loaded countries; `GET http://localhost:8000/gdp?country=UGA` filters
      to just that country
- [ ] Every list endpoint's response has the `items` / `total` / `limit` /
      `offset` envelope, and `total` reflects the full filtered match, not
      just the current page
- [ ] If `warehouse.duckdb` doesn't exist yet, any domain endpoint returns
      `503`, not a raw traceback / `500`
- [ ] `/news` still returns articles with no `source_name` (a legitimately
      sourceless article isn't dropped by the join)

Next milestone: Day 2, Step 7 — ML pipelines: train a forecasting model
against the warehouse, register it in MLflow, and add a `/predictions`
endpoint that loads the registered version.

## Repository layout

```
backend/       FastAPI service - app/routers/ (read-only domain endpoints
               over the warehouse, Day 2 Step 6), app/db.py (DuckDB access);
               ML-backed endpoints added Day 2 Step 7
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
               ingestion logic imported by DAGs), validation/ (Great
               Expectations suites, one per Silver dataset), warehouse/
               (loads validated Silver into the DuckDB star schema)
config/        Shared Pydantic settings used across services
tests/         Cross-service integration tests
docs/          Architecture and planning docs
scripts/       One-off ops scripts (e.g. Postgres multi-db init)
```
