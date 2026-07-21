# Global Economic Intelligence Platform

A data platform that ingests economic, weather, crypto, and news data,
transforms it through a medallion (Bronze/Silver/Gold) architecture, and
exposes it via API, dashboards, and ML forecasts.

This repository is being built as a series of small, testable milestones
rather than one large generation pass. See `docs/ARCHITECTURE.md` for the
current system diagram and `docs/ROADMAP.md`-equivalent (the 3-Day Sprint
plan) for what's built vs. what's next.

## Current status: Day 2 complete — Analytics and Machine Learning

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
  tests.

### Day 2 — Analytics and Machine Learning

Turning the clean Silver/warehouse data into intelligence added a real
World Bank **inflation** ingestion vertical first (connector, DAG, Spark
transform, GX suite, `fact_inflation`) — nothing upstream had inflation
data to build features or a `/predictions` model from before this.

- **Step 1/2 (warehouse repository layer + feature engineering)**:
  [`warehouse/schema/views.sql`](warehouse/schema/views.sql) adds one
  denormalized `view_*` per fact — each enriched with a lag column and a
  rolling-average column computed via a window function (e.g. `view_gdp`
  carries `lag1_gdp_usd` and `gdp_3yr_avg_usd`). This *is* the Day 2
  feature-engineering layer: rather than reopening the Day 1 Spark jobs,
  ML features are computed straight from the warehouse, so the API and
  the model trainers read identical numbers for identical rows without
  sharing Python code. Five `agg_*` views add genuine rollups (CAGR,
  monthly averages). Two thin "stored query" wrappers read these views —
  `pipelines/warehouse/repository.py` (whole DataFrames, for training) and
  `backend/app/repository.py` (paginated dict pages, for the API) — and
  the Step 6 routers were refactored onto the latter.
- **Step 3 (MLflow)**: `pipelines/ml/mlflow_utils.py` logs runs, registers
  model versions, and deploys via the modern **alias** API (`champion`)
  rather than the deprecated stage API, gated by a champion/challenger
  MAE comparison (`should_promote`). Fully testable against a local
  sqlite-backed tracking store — the Model Registry needs a
  database-backed store (sqlite qualifies; a plain file store doesn't),
  matching what the real deployment already uses (Postgres).
- **Step 4 (ML pipelines)**: `pipelines/ml/train.py` is one generic
  pooled-regression trainer (predict the next value from
  `[lag1, rolling_avg]`) shared by all four forecast domains — GDP,
  inflation, exchange rate, crypto — via a `ForecastSpec` registry in
  `pipelines/ml/models.py`, rather than four near-duplicate scripts.
  Holdout is the *last* chronological row per entity (country / currency
  pair / coin) — safe without a fallback split, since every row reaching
  the split already has a non-null lag feature.
- **Step 5 (nightly training DAG)**:
  `airflow/dags/_training_dag_factory.py` builds four DAGs
  (`train_{gdp,inflation,exchange_rate,crypto}_forecast`) around three
  tasks — `extract_train_evaluate` (fit + evaluate share in-memory state,
  so they're one task), `register`, `deploy` — passing only small
  metadata (a model URI, a version, an MAE) through Airflow's XCom, never
  the model object itself.
- **Step 6 (FastAPI, extended)**: added `/inflation`, `/predictions`
  (loads the champion model for a domain and applies it to an entity's
  latest feature row), `/models` (every registered model + champion
  version + metrics), `/pipeline-status` (latest run state per training
  DAG, read from Airflow's REST API). `/exchange-rates` was renamed to
  `/exchange`.
- **Step 7 (JWT auth)**: `backend/app/auth.py` — one admin credential
  from env vars, `POST /auth/login` issues an HS256 JWT, every router
  except `/health` and `/auth/login` itself requires a valid bearer
  token.
- **Step 8 (integration tests)**: `tests/test_integration/` — no
  mocking anywhere: a real in-memory warehouse feeds a real sklearn
  model into a real sqlite-backed MLflow registry, then a real FastAPI
  app serves a prediction from whatever's aliased `champion`; plus a
  real login → token → protected-call flow.

131 tests total (111 passing here; the other 20 are Spark transform tests
that fail in this sandbox purely from a pre-existing py4j/JVM environment
issue, unrelated to any of this code).

What does **not** exist yet (intentionally — separate milestones):
- React application UI (Day 3)
- Superset dashboards (Day 3)
- Wiring the validate → load step into the Airflow DAGs as an automatic
  gate after each Spark job. The pieces exist (`validate_silver.py` from
  Step 9, and `load_warehouse.py --validate` from Step 10 already chains
  them), but they aren't wired into a DAG yet — a natural next increment,
  deliberately deferred so it doesn't get thrown away if Day 3's needs
  change the schema.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

All 131 tests run offline. Connectors mock HTTP, ingestion/storage tests
mock boto3, Spark transform tests spin up a real local Spark session,
Great Expectations tests run against an ephemeral (in-memory) context,
warehouse tests load into an in-memory DuckDB, backend tests drive a
FastAPI `TestClient` against that same in-memory warehouse via a
dependency override, ML tests train real scikit-learn models against a
local sqlite-backed MLflow store, and the integration suite chains all of
the above together with no mocking at all — no persistent GX project,
warehouse file, or running server needed anywhere. Requires a JDK (11+)
on your machine for the
Spark tests.

## Getting started

```bash
cp .env.example .env
# edit .env with real secrets (Fernet key, passwords, Superset secret key,
# JWT secret key, backend admin username/password)

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

`/health` is the only backend route that doesn't need a token. Every other
route (Day 2, Step 7) requires logging in first:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "'"$AUTH_ADMIN_USERNAME"'", "password": "'"$AUTH_ADMIN_PASSWORD"'"}'
# -> {"access_token": "...", "token_type": "bearer"}

curl http://localhost:8000/gdp -H "Authorization: Bearer <access_token>"
```

## Acceptance criteria for this milestone

- [ ] `docker compose up -d --build` succeeds with no errors
- [ ] All containers report healthy / running (`docker compose ps`)
- [ ] Airflow UI is reachable and login works with `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`
- [ ] MinIO console shows `bronze`, `silver`, `gold` buckets already created
- [ ] `GET http://localhost:8000/health` returns `{"status": "ok", ...}`

Once all of the above are true, this milestone is done.

### Acceptance criteria for Step 4 (connectors)

- [ ] `pytest tests/test_connectors/ -v` passes (15/15)
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

- [ ] `pytest tests/test_spark/ -v` passes (20/20) using a real local
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

### Acceptance criteria for Step 1/2 (warehouse repository layer + features)

- [ ] `pytest tests/test_warehouse/ -v` passes (26/26) against an in-memory
      DuckDB, including `test_views.py`
- [ ] After loading Step 10 data, `SELECT * FROM view_gdp` (or any other
      `view_*`) returns rows with a non-null `lag1_*`/rolling-average
      column for every row except an entity's first observation
- [ ] `SELECT * FROM agg_gdp_by_country` returns one row per country with a
      computed `gdp_cagr`
- [ ] `pytest tests/test_connectors/test_world_bank_inflation.py
      tests/test_validation/test_world_bank_inflation_suite.py
      tests/test_warehouse/test_world_bank_inflation_load.py -v` passes
      (6/6) - the new inflation vertical

### Acceptance criteria for Step 3 (MLflow)

- [ ] `pytest tests/test_ml/test_mlflow_utils.py -v` passes against a
      local sqlite-backed tracking store, no live server required
- [ ] `log_run` + `register_model` produce a new registered model version;
      `promote_to_champion` + `champion_metric` + `should_promote` gate
      promotion correctly on MAE
- [ ] `docker compose up -d --build` followed by opening
      `http://localhost:5000` shows the MLflow UI

### Acceptance criteria for Step 4 (ML pipelines)

- [ ] `pytest tests/test_ml/test_train.py -v` passes for all four
      `FORECAST_SPECS` domains (gdp, inflation, exchange_rate, crypto)
- [ ] Holdout is the last chronological row per entity, not a random split
- [ ] Training with fewer than `MIN_TRAINING_ROWS` usable rows raises
      `InsufficientTrainingDataError` rather than fitting on too little data

### Acceptance criteria for Step 5 (nightly training DAG)

- [ ] `docker compose up -d --build` and `airflow dags list` shows all
      four `train_*_forecast` DAGs with no import errors
- [ ] Manually triggering `train_gdp_forecast` completes all three tasks
      (`extract_train_evaluate`, `register`, `deploy`) and a new version
      appears for `gdp_forecast` in the MLflow UI
- [ ] Triggering the same DAG again only moves the `champion` alias if the
      new run's MAE beats the current champion's

### Acceptance criteria for Step 6 (FastAPI domain + ML endpoints)

- [ ] `pytest tests/test_backend/ -v` passes (34/34) against an in-memory
      DuckDB via a `TestClient` + dependency override
- [ ] With a real warehouse loaded (Step 10), logging in (Step 7) and
      calling `GET http://localhost:8000/gdp?country=UGA` filters to just
      that country; `GET .../inflation?country=UGA` does the same for
      inflation
- [ ] Every list endpoint's response has the `items` / `total` / `limit` /
      `offset` envelope
- [ ] Once a model has been trained and promoted (Step 5),
      `GET .../predictions?domain=gdp&country=UGA` returns a numeric
      `predicted_value`; before that, it returns `404`, not `500`
- [ ] `GET .../models` lists every registered model with its champion
      version and metrics; `GET .../pipeline-status` reports the latest
      run state for all four training DAGs

### Acceptance criteria for Step 7 (JWT auth)

- [ ] `POST /auth/login` with the configured admin credential returns a
      bearer token; with the wrong password, `401`
- [ ] Any endpoint other than `/health` and `/auth/login` returns `401`
      without a token, and succeeds with one from `/auth/login`

### Acceptance criteria for Step 8 (integration tests)

- [ ] `pytest tests/test_integration/ -v` passes (5/5) with no mocking -
      a real trained model served through a real API call, and a real
      login → protected-call flow

Day 2 is complete: warehouse views and features → MLflow tracking and
registry → four forecast models → a nightly training DAG → a
JWT-protected FastAPI serving both data and predictions.

Next milestone: Day 3 — the React frontend and Superset dashboards.

## Repository layout

```
backend/       FastAPI service - app/routers/ (domain + ML endpoints),
               app/db.py + app/repository.py (DuckDB access/queries),
               app/mlflow_client.py + app/airflow_client.py (thin wrappers
               around MLflow's registry and Airflow's REST API),
               app/auth.py (Day 2, Step 7 JWT). No dependency on pipelines/.
frontend/      React app (full UI added Day 3)
airflow/       DAGs - ingest_*.py (Day 1, Step 5) and train_*_forecast.py
               (Day 2, Step 5, via _training_dag_factory.py), plugins,
               custom Airflow image
spark/         jobs/ (one ETL entrypoint per source, transforms/ holding
               the pure clean/normalize/merge/feature-engineer logic),
               custom Spark image
warehouse/     DuckDB file + schema/ (star_schema.sql, views.sql)
data/          Local mirror of bronze/silver/gold (MinIO is source of truth)
models/        Trained model artifacts (MLflow registry is source of truth)
pipelines/     connectors/ (World Bank + inflation, Open-Meteo, ExchangeRate,
               CoinGecko, NewsAPI), storage/ (MinIO Bronze writer), tasks/
               (shared ingestion logic imported by DAGs), validation/ (Great
               Expectations suites, one per Silver dataset), warehouse/
               (loads validated Silver into the DuckDB star schema; Day 2
               repository.py reads the views for ML feature extraction),
               ml/ (Day 2: mlflow_utils.py, train.py, models.py, pipeline.py)
config/        Shared Pydantic settings used across services
tests/         Cross-service integration tests, including test_ml/ and
               test_integration/ (Day 2)
docs/          Architecture and planning docs
scripts/       One-off ops scripts (e.g. Postgres multi-db init)
```
