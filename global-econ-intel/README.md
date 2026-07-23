# Global Economic Intelligence Platform

A full-stack data platform that ingests real-time economic, weather, crypto,
and news data; transforms it through a Bronze → Silver → Gold (medallion)
pipeline; trains forecasting models on top of it; and serves the result
through an API, a React dashboard, embedded BI dashboards, and live
predictions.

Everything in this repo runs against **real external data** — World Bank
GDP/inflation, live exchange rates, current crypto prices, weather
observations, and news headlines — orchestrated end-to-end by Airflow and
Spark, not sample/seed data.

![Architecture](docs/Architecture.png)

## What it does

- **Ingests** six real-world sources on a daily schedule: World Bank GDP,
  World Bank inflation, Open-Meteo weather, live exchange rates, CoinGecko
  crypto prices, and NewsAPI headlines.
- **Transforms** raw JSON into validated, deduplicated Parquet through a
  Bronze → Silver pipeline (Spark), gated by Great Expectations data-quality
  suites.
- **Loads** the validated Silver layer into a DuckDB star schema — one
  conformed date dimension, one dimension per entity, one fact table per
  source.
- **Trains** forecasting models (GDP, inflation, exchange rate, crypto)
  nightly, tracked and versioned in MLflow, auto-promoted to a `champion`
  alias when they beat the current model.
- **Serves** all of it through a JWT-authenticated FastAPI backend: paginated
  data endpoints, live predictions from whichever model is deployed, model
  registry status, and pipeline health.
- **Visualizes** it in a React dashboard with real embedded Superset
  dashboards (guest-token auth, not a public iframe), plus a monitoring page
  for every service and pipeline in the stack.

## Architecture at a glance

```
 Connectors → Airflow (ingest) → Bronze (MinIO)
                     │
                     ▼
              Spark ETL + Great Expectations → Silver (MinIO)
                     │
                     ▼
              DuckDB star schema (warehouse)
                 │                     │
                 ▼                     ▼
        FastAPI backend         MLflow (train/register/deploy)
                 │                     │
                 ▼                     ▼
        React frontend  ◄──── Predictions, Superset dashboards
```

Each `ingest_*` Airflow DAG runs the full chain — fetch → Bronze → Spark ETL
→ Silver → warehouse load — daily, with no manual steps in between. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system diagram
and design notes, and [`docs/Schema.png`](docs/Schema.png) for the warehouse
star schema.

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow (CeleryExecutor) |
| Processing | Apache Spark (PySpark) |
| Data quality | Great Expectations |
| Object storage | MinIO (S3-compatible) |
| Warehouse | DuckDB |
| ML tracking/registry | MLflow |
| BI dashboards | Apache Superset (embedded via guest tokens) |
| Backend | FastAPI, JWT auth |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts |
| Metadata store | PostgreSQL |
| Queue/broker | Redis |
| Everything | Docker Compose |

## Getting started

**Prerequisites:** Docker Desktop (or another Compose-compatible engine).

```bash
cp .env.example .env
# fill in real secrets - Fernet key, passwords, Superset secret key, JWT
# secret key, backend admin credentials. Generator commands are inline as
# comments in .env.example. A free NewsAPI key (newsapi.org) is the only
# external API key required.

docker compose up -d --build
```

Once everything is healthy:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API health check | http://localhost:8000/health |
| Airflow | http://localhost:8080 |
| MLflow | http://localhost:5000 |
| Superset | http://localhost:8088 |
| MinIO Console | http://localhost:9001 |
| Spark Master UI | http://localhost:8081 |

Log in with the `AUTH_ADMIN_USERNAME` / `AUTH_ADMIN_PASSWORD` you set in
`.env`. Every backend route except `/health` and `/auth/login` requires that
session.

Superset's six example dashboards (GDP, Inflation, Weather, Crypto,
Exchange, Forecasts) need a one-time import — see
[`superset/dashboards/README.md`](superset/dashboards/README.md).

### Running locally without Docker (faster iteration)

For quick frontend/backend iteration without the full stack - no
Airflow/Spark/Superset, just the API and UI against a locally populated
warehouse:

```bash
# 1. Populate a local warehouse with real data (World Bank, Open-Meteo,
#    exchange rates, CoinGecko - all keyless; news is skipped, no key here)
pip install -r requirements-dev.txt
python scripts/load_local_demo_data.py

# 2. Backend
cd backend
cp .env.example .env
uvicorn app.main:app --reload

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

This path can't do everything the full stack can: no Superset dashboards,
no `/predictions` (no MLflow server means no champion model), and
`/pipeline-status` reports Airflow as unreachable - both handle that
gracefully rather than erroring. It's meant for fast UI/API iteration, not
a full local deployment.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Connectors mock HTTP; Spark tests spin up a real local Spark session
(requires a JDK 11+ locally); ML tests train real scikit-learn models
against a local sqlite-backed MLflow store; the integration suite chains a
real warehouse → real model → real API call with no mocking. See
[`docs/API.md`](docs/API.md) for the full endpoint reference.

## Repository layout

```
airflow/       Custom Airflow image + DAGs: one combined ingest→ETL→load
               DAG per source, plus nightly model training DAGs
spark/         Custom Spark image + ETL jobs (one per source) and their
               pure transform logic
pipelines/     Source connectors, Bronze writer, Great Expectations suites,
               warehouse loader, and the ML training/registry code shared
               by the Airflow DAGs
warehouse/     DuckDB file + star schema DDL and views
backend/       FastAPI service - domain + ML endpoints, JWT auth, thin
               clients for MLflow/Airflow/Superset
frontend/      React + TypeScript + Tailwind app
superset/      Superset config (embedding, guest tokens) + declarative
               dashboard definitions
config/        Shared settings used across services
mlflow/        Custom MLflow tracking-server image
tests/         Unit, integration, and cross-service tests
docs/          Architecture, API reference, deployment guide
scripts/       One-off ops scripts
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — full system design
- [`docs/API.md`](docs/API.md) — backend endpoint reference
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — cloud deployment guide
