# Architecture

## System diagram

```mermaid
flowchart LR
    subgraph Sources["External APIs"]
        WB[World Bank]
        OM[Open-Meteo]
        FX[ExchangeRate]
        CG[CoinGecko]
        NA[NewsAPI]
    end

    subgraph Ingest["Airflow"]
        DAGs[Ingestion DAGs]
    end

    subgraph Storage["MinIO - Medallion Architecture"]
        Bronze[(Bronze - raw JSON)]
        Silver[(Silver - cleaned Parquet)]
        Gold[(Gold - features & aggregates)]
    end

    subgraph Compute["Spark"]
        ETL[PySpark ETL]
        GE[Great Expectations]
    end

    subgraph Warehouse["DuckDB"]
        Star[(Star Schema:
        Facts + Dimensions)]
    end

    subgraph ML["MLflow"]
        Track[Tracking + Registry]
    end

    subgraph App["Application Layer"]
        API[FastAPI Backend]
        UI[React Frontend]
        BI[Superset Dashboards]
    end

    Sources --> DAGs --> Bronze
    Bronze --> ETL --> GE --> Silver
    Silver --> Star
    Star --> API
    Silver --> Track
    Track --> API
    API --> UI
    Star --> BI
    Gold -.future.-> Track
```

## Why this shape

- **Medallion storage (Bronze/Silver/Gold in MinIO)** keeps raw data
  immutable and separates "what we received" from "what we trust."
- **DuckDB as the warehouse** avoids standing up a full Postgres/Snowflake
  analytics stack for what is, at this stage, a single-node analytical
  workload — it reads Parquet directly out of MinIO.
- **Airflow orchestrates, Spark transforms** — DAGs stay thin (trigger +
  monitor), heavy lifting lives in versioned PySpark jobs that can be
  tested independently of the scheduler.
- **MLflow sits beside, not inside, the API** — models are trained and
  registered out-of-band; the API only ever loads a registered model
  version, it never trains one.

## Warehouse star schema (Day 1, Step 10)

The validated Silver layer is loaded into a DuckDB star schema. The DDL is in
[`warehouse/schema/star_schema.sql`](../warehouse/schema/star_schema.sql); the
loader is [`pipelines/warehouse/`](../pipelines/warehouse/).

```mermaid
erDiagram
    dim_date        ||--o{ fact_exchange_rate : date_key
    dim_date        ||--o{ fact_weather       : date_key
    dim_date        ||--o{ fact_crypto        : date_key
    dim_date        ||--o{ fact_news          : date_key
    dim_currency    ||--o{ fact_exchange_rate : "base + quote"
    dim_location    ||--o{ fact_weather       : location_key
    dim_coin        ||--o{ fact_crypto        : coin_key
    dim_news_source ||--o{ fact_news          : news_source_key
    dim_country     ||--o{ fact_gdp           : country_key
```

- **`dim_date` is conformed** — every daily-grain fact shares it. `fact_gdp` is
  the exception: GDP is annual, so it carries `year` directly rather than
  joining a daily date dimension.
- **`dim_currency` is conformed across both sides of a pair** —
  `fact_exchange_rate` has two FKs (`base_currency_key`, `quote_currency_key`)
  into the one currency dimension.
- **Loads are idempotent** — dimensions upsert on their natural key onto a
  stable surrogate key; facts upsert on their grain. Re-loading the same Silver
  dataset (a DAG retry, a rolling-window re-pull) leaves the warehouse
  identical, extending the same guarantee Bronze and the Spark merge step
  already provide.

## Explicit non-goals for Day 1, Step 1

- No connector logic (Day 1, Step 4)
- No DAG business logic beyond a proven "hello world" trigger (Day 1, Step 5)
- No Spark transformation logic (Day 1, Step 8)
- No FastAPI domain routes (Day 2, Step 6)
- No React UI (Day 3, Step 1)

This document will be updated as each milestone lands.
