# Global Economic Intelligence Platform

A data platform that ingests economic, weather, crypto, and news data,
transforms it through a medallion (Bronze/Silver/Gold) architecture, and
exposes it via API, dashboards, and ML forecasts.

This repository is being built as a series of small, testable milestones
rather than one large generation pass. See `docs/ARCHITECTURE.md` for the
current system diagram and `docs/ROADMAP.md`-equivalent (the 3-Day Sprint
plan) for what's built vs. what's next.

## Current status: Day 1, Step 4 — API connectors

Completed so far:
- **Step 1**: `docker-compose.yml`, folder structure, `.env.example`,
  placeholder Dockerfiles for services with no logic yet
- **Step 4**: `pipelines/connectors/` — one connector per source
  (World Bank, Open-Meteo, ExchangeRate, CoinGecko, NewsAPI), each with
  retries (exponential backoff), structured JSON logging, Pydantic
  response validation, and pagination where the source supports it.
  14 passing unit tests in `tests/test_connectors/` (network calls
  mocked — see "Running tests" below).

What does **not** exist yet (intentionally — separate milestones):
- Airflow ingestion DAGs that actually call these connectors and write
  to MinIO's Bronze bucket (Step 5)
- PySpark ETL jobs (Step 8)
- Great Expectations validation suites (Step 9)
- DuckDB star schema (Step 10)
- ML pipelines / FastAPI domain endpoints (Day 2)
- React application UI (Day 3)
- Superset dashboards (Day 3)

## Running the connector tests

```bash
pip install -r requirements-dev.txt
pytest tests/test_connectors/ -v
```

All 14 tests run offline against mocked HTTP responses, so no API keys
or network access are needed to verify connector logic.

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

Next milestone: Day 1, Step 5 — Airflow DAGs that call
`CONNECTOR_REGISTRY` and write raw JSON to MinIO's Bronze bucket.

## Repository layout

```
backend/       FastAPI service (domain endpoints added Day 2)
frontend/      React app (full UI added Day 3)
airflow/       DAGs, plugins, custom Airflow image
spark/         PySpark ETL jobs, custom Spark image
warehouse/     DuckDB file + star schema DDL
data/          Local mirror of bronze/silver/gold (MinIO is source of truth)
models/        Trained model artifacts (MLflow registry is source of truth)
pipelines/     connectors/ (World Bank, Open-Meteo, ExchangeRate, CoinGecko,
               NewsAPI) + shared transformation code, importable by Airflow
config/        Shared Pydantic settings used across services
tests/         Cross-service integration tests
docs/          Architecture and planning docs
scripts/       One-off ops scripts (e.g. Postgres multi-db init)
```
