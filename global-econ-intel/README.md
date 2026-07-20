# Global Economic Intelligence Platform

A data platform that ingests economic, weather, crypto, and news data,
transforms it through a medallion (Bronze/Silver/Gold) architecture, and
exposes it via API, dashboards, and ML forecasts.

This repository is being built as a series of small, testable milestones
rather than one large generation pass. See `docs/ARCHITECTURE.md` for the
current system diagram and `docs/ROADMAP.md`-equivalent (the 3-Day Sprint
plan) for what's built vs. what's next.

## Current status: Day 1, Step 5 — Airflow ingestion DAGs

Completed so far:
- **Step 1**: `docker-compose.yml`, folder structure, `.env.example`,
  placeholder Dockerfiles for services with no logic yet
- **Step 4**: `pipelines/connectors/` — five source connectors with
  retries, structured logging, validation, and pagination
- **Step 5**: `airflow/dags/` — one DAG per source
  (`ingest_world_bank`, `ingest_open_meteo`, `ingest_exchange_rate`,
  `ingest_coingecko`, `ingest_newsapi`), each fetching through its
  connector and writing raw JSON to the Bronze bucket via
  `pipelines/storage/minio_client.py`. Writes are idempotent — reruns
  for the same day overwrite the same object key instead of
  duplicating data. 19 passing unit tests total (5 new, covering the
  storage layer and ingestion orchestration).

What does **not** exist yet (intentionally — separate milestones):
- PySpark ETL jobs reading Bronze → Silver (Step 8)
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

All 19 tests run offline — connectors mock HTTP, and the ingestion/storage
tests mock boto3 — so no live API keys, MinIO, or Airflow install are
needed to verify the logic itself.

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

Next milestone: Day 1, Step 8 — PySpark ETL reading Bronze → cleaning,
normalizing, merging, feature engineering → writing Silver Parquet.
(Step 6/7 — bucket creation and "store raw JSON, test" — are already
satisfied by `createbuckets` in `docker-compose.yml` and Step 5 above.)

## Repository layout

```
backend/       FastAPI service (domain endpoints added Day 2)
frontend/      React app (full UI added Day 3)
airflow/       DAGs (one per source), plugins, custom Airflow image
spark/         PySpark ETL jobs, custom Spark image
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
