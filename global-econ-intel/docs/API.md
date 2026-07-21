# API reference

The FastAPI backend generates full interactive API documentation from the
same Pydantic schemas that validate every request/response - that's the
authoritative reference, not this file:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Raw OpenAPI schema**: `http://localhost:8000/openapi.json`

This page is a quick map of what exists and how auth works, so you don't
have to open Swagger just to remember an endpoint's name.

## Authentication (Day 2, Step 7)

Every route below requires a bearer token except `/health` and
`/auth/login` itself.

```
POST /auth/login
  body: {"username": "...", "password": "..."}
  -> {"access_token": "...", "token_type": "bearer"}
```

Send it back as `Authorization: Bearer <access_token>` on every other call.
Tokens are short-lived HS256 JWTs (`JWT_EXPIRE_MINUTES`, default 60) - there
is no refresh-token flow; log in again once it expires.

## Domain endpoints (Day 1/2)

Read-only, backed by the DuckDB warehouse's `view_*` views. All support a
shared pagination envelope (`items`, `total`, `limit`, `offset`) and
domain-appropriate filters (see Swagger for the exact query params).

| Method | Path              | Source                                    |
|--------|-------------------|--------------------------------------------|
| GET    | `/countries`       | `dim_country`                              |
| GET    | `/gdp`             | `view_gdp` (World Bank)                    |
| GET    | `/inflation`       | `view_inflation` (World Bank)               |
| GET    | `/exchange`        | `view_exchange_rate`                       |
| GET    | `/weather`         | `view_weather` (Open-Meteo)                 |
| GET    | `/crypto`          | `view_crypto` (CoinGecko)                   |
| GET    | `/news`            | `view_news` (NewsAPI)                       |

## ML endpoints (Day 2, Step 3-6)

| Method | Path                | What it does                                                        |
|--------|---------------------|----------------------------------------------------------------------|
| GET    | `/predictions`      | Loads the `champion`-aliased MLflow model for `?domain=` and scores it against the entity's latest feature row (`?country=`, `?base=`/`?quote=`, or `?coin_id=` depending on domain) |
| GET    | `/models`           | Every registered model: name, latest version, champion version, champion's metrics |
| GET    | `/pipeline-status`  | Latest Airflow run state for each of the four nightly training DAGs   |

`/predictions` domains: `gdp`, `inflation` (both take `?country=`),
`exchange_rate` (`?base=&?quote=`), `crypto` (`?coin_id=`).

## Day 3 additions

| Method | Path                     | What it does                                                   |
|--------|--------------------------|-------------------------------------------------------------------|
| GET    | `/superset/guest-token`  | Mints a Superset guest token scoped to one dashboard (`?dashboard=gdp\|inflation\|weather\|crypto\|exchange\|forecasts`) |
| GET    | `/monitoring/services`   | Reachability check for MinIO, MLflow, Airflow, and this API itself |

## Error shape

Every non-2xx response is `{"detail": "..."}` (FastAPI's default), which
the frontend's `ApiError` class surfaces directly. Status codes used
beyond the obvious 400/401/404: `503` when the warehouse file hasn't been
loaded yet, `502` when an upstream service (Superset) is unreachable.
