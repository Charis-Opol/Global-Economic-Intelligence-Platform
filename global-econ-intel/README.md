# Global Economic Intelligence Platform

A data platform that ingests economic, weather, crypto, and news data,
transforms it through a medallion (Bronze/Silver/Gold) architecture, and
exposes it via API, dashboards, and ML forecasts.

This repository is being built as a series of small, testable milestones
rather than one large generation pass. See `docs/ARCHITECTURE.md` for the
current system diagram and `docs/ROADMAP.md`-equivalent (the 3-Day Sprint
plan) for what's built vs. what's next.

## Current status: Day 1, Step 1 — Architecture scaffold

What exists right now:
- `docker-compose.yml` wiring every planned container together
- Folder structure for every layer of the system
- Environment variable template (`.env.example`)
- Placeholder Dockerfiles/entrypoints for services with no logic yet
  (backend, frontend, mlflow, spark)

What does **not** exist yet (intentionally — these are separate milestones):
- API connectors (World Bank, Open-Meteo, ExchangeRate, CoinGecko, NewsAPI)
- Airflow ingestion DAGs
- PySpark ETL jobs
- Great Expectations validation suites
- DuckDB star schema
- ML pipelines / FastAPI domain endpoints
- React application UI
- Superset dashboards

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

Once all of the above are true, this milestone is done — commit it, then
move to Day 1, Step 4 (API connectors) as its own prompt.

## Repository layout

```
backend/       FastAPI service (domain endpoints added Day 2)
frontend/      React app (full UI added Day 3)
airflow/       DAGs, plugins, custom Airflow image
spark/         PySpark ETL jobs, custom Spark image
warehouse/     DuckDB file + star schema DDL
data/          Local mirror of bronze/silver/gold (MinIO is source of truth)
models/        Trained model artifacts (MLflow registry is source of truth)
pipelines/     Shared connector + transformation code, importable by Airflow
config/        Shared Pydantic settings used across services
tests/         Cross-service integration tests
docs/          Architecture and planning docs
scripts/       One-off ops scripts (e.g. Postgres multi-db init)
```
