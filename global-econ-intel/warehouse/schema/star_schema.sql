-- ============================================================================
-- Global Economic Intelligence Platform - DuckDB star schema (Day 1, Step 10)
-- ============================================================================
--
-- The canonical warehouse DDL. Loaded and executed by
-- `pipelines/warehouse/schema.py`; also readable directly by anything that
-- needs to inspect the schema (Superset, the Day 2 backend).
--
-- Design:
--   * One conformed `dim_date` shared by every daily-grain fact.
--   * One dimension per real-world entity (country, currency, coin,
--     location, news source), each with an integer surrogate key from a
--     sequence and a UNIQUE natural key so loads can upsert idempotently.
--   * One fact per source, at the grain its Silver dataset already dedupes
--     to. GDP is annual, so `fact_gdp` carries `year` directly instead of a
--     `date_key` - not every fact shares the daily date dimension, only the
--     ones whose grain actually is a calendar day.
--
-- Every statement is idempotent (IF NOT EXISTS), so applying this file to an
-- existing warehouse is a no-op - safe to run before every load.

-- ---------------------------------------------------------------------------
-- Conformed date dimension
-- ---------------------------------------------------------------------------
-- `date_key` is a "smart" YYYYMMDD integer rather than a surrogate sequence:
-- it is deterministic from the date, so a rerun computes the same key and the
-- ON CONFLICT upsert stays idempotent without a lookup.
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INTEGER PRIMARY KEY,        -- YYYYMMDD, e.g. 20260721
    full_date   DATE    NOT NULL UNIQUE,
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  VARCHAR NOT NULL,
    day         INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,           -- Sunday = 0 .. Saturday = 6
    day_name    VARCHAR NOT NULL,
    is_weekend  BOOLEAN NOT NULL
);

-- ---------------------------------------------------------------------------
-- Country dimension (World Bank)
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_country_key START 1;
CREATE TABLE IF NOT EXISTS dim_country (
    country_key  INTEGER PRIMARY KEY DEFAULT nextval('seq_country_key'),
    country_iso3 VARCHAR NOT NULL UNIQUE,
    country_name VARCHAR
);

-- ---------------------------------------------------------------------------
-- Currency dimension (Exchange Rate) - conformed: a currency is a currency
-- whether it appears as the base or the quote side of a pair.
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_currency_key START 1;
CREATE TABLE IF NOT EXISTS dim_currency (
    currency_key  INTEGER PRIMARY KEY DEFAULT nextval('seq_currency_key'),
    currency_code VARCHAR NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- Coin dimension (CoinGecko)
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_coin_key START 1;
CREATE TABLE IF NOT EXISTS dim_coin (
    coin_key INTEGER PRIMARY KEY DEFAULT nextval('seq_coin_key'),
    coin_id  VARCHAR NOT NULL UNIQUE,
    symbol   VARCHAR,
    name     VARCHAR
);

-- ---------------------------------------------------------------------------
-- Location dimension (Open-Meteo) - one point per (lat, lon) we pull weather
-- for. The coordinates come straight from the source unchanged, so an exact
-- (lat, lon) match is a stable natural key.
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_location_key START 1;
CREATE TABLE IF NOT EXISTS dim_location (
    location_key INTEGER PRIMARY KEY DEFAULT nextval('seq_location_key'),
    latitude     DOUBLE NOT NULL,
    longitude    DOUBLE NOT NULL,
    UNIQUE (latitude, longitude)
);

-- ---------------------------------------------------------------------------
-- News source dimension (NewsAPI)
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_news_source_key START 1;
CREATE TABLE IF NOT EXISTS dim_news_source (
    news_source_key INTEGER PRIMARY KEY DEFAULT nextval('seq_news_source_key'),
    source_name     VARCHAR NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- GDP: annual grain, so `year` lives on the fact rather than a date_key.
CREATE TABLE IF NOT EXISTS fact_gdp (
    country_key     INTEGER NOT NULL REFERENCES dim_country (country_key),
    indicator_id    VARCHAR NOT NULL,
    year            INTEGER NOT NULL,
    gdp_usd         DOUBLE,
    gdp_growth_rate DOUBLE,
    PRIMARY KEY (country_key, indicator_id, year)
);

-- Inflation (Day 2): same grain and shape as fact_gdp - a separate table
-- rather than folding into fact_gdp, since "gdp_usd" would be a misnomer
-- for an inflation percentage. Shares dim_country and indicator_id follows
-- the same convention (World Bank indicator code, e.g. FP.CPI.TOTL.ZG).
CREATE TABLE IF NOT EXISTS fact_inflation (
    country_key     INTEGER NOT NULL REFERENCES dim_country (country_key),
    indicator_id    VARCHAR NOT NULL,
    year            INTEGER NOT NULL,
    inflation_pct   DOUBLE,
    inflation_trend DOUBLE,
    PRIMARY KEY (country_key, indicator_id, year)
);

-- Exchange rate: one row per (base, quote, day). Two FKs into the one
-- conformed currency dimension.
CREATE TABLE IF NOT EXISTS fact_exchange_rate (
    base_currency_key  INTEGER NOT NULL REFERENCES dim_currency (currency_key),
    quote_currency_key INTEGER NOT NULL REFERENCES dim_currency (currency_key),
    date_key           INTEGER NOT NULL REFERENCES dim_date (date_key),
    rate               DOUBLE,
    exchange_momentum  DOUBLE,
    PRIMARY KEY (base_currency_key, quote_currency_key, date_key)
);

-- Weather: one row per (location, day).
CREATE TABLE IF NOT EXISTS fact_weather (
    location_key        INTEGER NOT NULL REFERENCES dim_location (location_key),
    date_key            INTEGER NOT NULL REFERENCES dim_date (date_key),
    temp_max_c          DOUBLE,
    temp_min_c          DOUBLE,
    precipitation_mm    DOUBLE,
    precip_30d_avg_mm   DOUBLE,
    rainfall_anomaly_mm DOUBLE,
    PRIMARY KEY (location_key, date_key)
);

-- Crypto: one row per (coin, day).
CREATE TABLE IF NOT EXISTS fact_crypto (
    coin_key             INTEGER NOT NULL REFERENCES dim_coin (coin_key),
    date_key             INTEGER NOT NULL REFERENCES dim_date (date_key),
    price_usd            DOUBLE,
    market_cap_usd       DOUBLE,
    volume_usd           DOUBLE,
    price_change_pct_24h DOUBLE,
    volatility_7d        DOUBLE,
    PRIMARY KEY (coin_key, date_key)
);

-- News: article grain. `url` is the degenerate dimension and natural key.
-- `news_source_key` is nullable because a Silver article can legitimately
-- have no source name (it is dropped from `dim_news_source`, not invented).
CREATE TABLE IF NOT EXISTS fact_news (
    url               VARCHAR PRIMARY KEY,
    news_source_key   INTEGER REFERENCES dim_news_source (news_source_key),
    date_key          INTEGER NOT NULL REFERENCES dim_date (date_key),
    title             VARCHAR,
    author            VARCHAR,
    description       VARCHAR,
    published_at      TIMESTAMP,
    articles_that_day BIGINT
);
