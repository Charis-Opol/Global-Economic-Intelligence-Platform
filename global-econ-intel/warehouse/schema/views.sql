-- ============================================================================
-- Global Economic Intelligence Platform - warehouse repository layer
-- (Day 2, Step 1: SQL views, aggregations, stored queries)
-- ============================================================================
--
-- Applied after star_schema.sql (see `pipelines/warehouse/schema.py`), so
-- every view below can assume the fact/dimension tables already exist.
--
-- Two kinds of view:
--   * `view_*`  - one row per fact row, denormalized (natural keys resolved
--     to human-readable names) and enriched with a lag + rolling-average
--     column computed via a window function. This is Day 2's feature
--     engineering layer: rather than reopening the Day 1 Spark transforms,
--     ML-ready features live here, computed straight from the warehouse.
--     The backend's read endpoints query these same views, so the API and
--     the model trainers see identical numbers for identical rows.
--   * `agg_*`   - one row per entity (or entity+month), a genuine GROUP BY
--     rollup: latest/first value, CAGR, monthly averages. These answer
--     "how has this country/pair/coin done overall" questions a per-row
--     view can't.
--
-- Every statement is idempotent (CREATE VIEW IF NOT EXISTS), matching
-- star_schema.sql, so re-applying this file is always safe.

-- ---------------------------------------------------------------------------
-- Per-row views (denormalized + one lag + one rolling-average feature)
-- ---------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS view_gdp AS
SELECT
    c.country_iso3,
    c.country_name,
    f.indicator_id,
    f.year,
    f.gdp_usd,
    f.gdp_growth_rate,
    LAG(f.gdp_usd) OVER (PARTITION BY f.country_key ORDER BY f.year) AS lag1_gdp_usd,
    AVG(f.gdp_usd) OVER (
        PARTITION BY f.country_key ORDER BY f.year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS gdp_3yr_avg_usd
FROM fact_gdp f
JOIN dim_country c USING (country_key);

CREATE VIEW IF NOT EXISTS view_inflation AS
SELECT
    c.country_iso3,
    c.country_name,
    f.indicator_id,
    f.year,
    f.inflation_pct,
    f.inflation_trend,
    LAG(f.inflation_pct) OVER (PARTITION BY f.country_key ORDER BY f.year) AS lag1_inflation_pct,
    AVG(f.inflation_pct) OVER (
        PARTITION BY f.country_key ORDER BY f.year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS inflation_3yr_avg_pct
FROM fact_inflation f
JOIN dim_country c USING (country_key);

CREATE VIEW IF NOT EXISTS view_exchange_rate AS
SELECT
    b.currency_code AS base_code,
    q.currency_code AS currency,
    d.full_date AS date,
    f.rate,
    f.exchange_momentum,
    LAG(f.rate) OVER (
        PARTITION BY f.base_currency_key, f.quote_currency_key ORDER BY d.full_date
    ) AS lag1_rate,
    AVG(f.rate) OVER (
        PARTITION BY f.base_currency_key, f.quote_currency_key ORDER BY d.full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rate_7d_avg
FROM fact_exchange_rate f
JOIN dim_currency b ON b.currency_key = f.base_currency_key
JOIN dim_currency q ON q.currency_key = f.quote_currency_key
JOIN dim_date d USING (date_key);

CREATE VIEW IF NOT EXISTS view_weather AS
SELECT
    l.latitude,
    l.longitude,
    d.full_date AS date,
    f.temp_max_c,
    f.temp_min_c,
    f.precipitation_mm,
    f.precip_30d_avg_mm,
    f.rainfall_anomaly_mm,
    AVG(f.temp_max_c) OVER (
        PARTITION BY f.location_key ORDER BY d.full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS temp_max_7d_avg_c
FROM fact_weather f
JOIN dim_location l USING (location_key)
JOIN dim_date d USING (date_key);

CREATE VIEW IF NOT EXISTS view_crypto AS
SELECT
    c.coin_id,
    c.symbol,
    c.name,
    d.full_date AS date,
    f.price_usd,
    f.market_cap_usd,
    f.volume_usd,
    f.price_change_pct_24h,
    f.volatility_7d,
    LAG(f.price_usd) OVER (PARTITION BY f.coin_key ORDER BY d.full_date) AS lag1_price_usd,
    AVG(f.price_usd) OVER (
        PARTITION BY f.coin_key ORDER BY d.full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS price_7d_avg_usd
FROM fact_crypto f
JOIN dim_coin c USING (coin_key)
JOIN dim_date d USING (date_key);

CREATE VIEW IF NOT EXISTS view_news AS
SELECT
    f.url,
    ns.source_name,
    f.title,
    f.author,
    f.description,
    f.published_at,
    d.full_date AS date,
    f.articles_that_day
FROM fact_news f
LEFT JOIN dim_news_source ns USING (news_source_key)
JOIN dim_date d USING (date_key);

-- ---------------------------------------------------------------------------
-- Aggregation views (one row per entity, or entity+month)
-- ---------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS agg_gdp_by_country AS
SELECT
    c.country_iso3,
    c.country_name,
    COUNT(*) AS years_reported,
    MIN(f.year) AS first_year,
    MAX(f.year) AS latest_year,
    ARG_MIN(f.gdp_usd, f.year) AS first_year_gdp_usd,
    ARG_MAX(f.gdp_usd, f.year) AS latest_gdp_usd,
    AVG(f.gdp_growth_rate) AS avg_gdp_growth_rate,
    CASE
        WHEN ARG_MIN(f.gdp_usd, f.year) > 0 AND MAX(f.year) > MIN(f.year)
        THEN POWER(
            ARG_MAX(f.gdp_usd, f.year) / ARG_MIN(f.gdp_usd, f.year),
            1.0 / (MAX(f.year) - MIN(f.year))
        ) - 1
    END AS gdp_cagr
FROM fact_gdp f
JOIN dim_country c USING (country_key)
GROUP BY c.country_iso3, c.country_name;

CREATE VIEW IF NOT EXISTS agg_inflation_by_country AS
SELECT
    c.country_iso3,
    c.country_name,
    COUNT(*) AS years_reported,
    MAX(f.year) AS latest_year,
    ARG_MAX(f.inflation_pct, f.year) AS latest_inflation_pct,
    AVG(f.inflation_pct) AS avg_inflation_pct
FROM fact_inflation f
JOIN dim_country c USING (country_key)
GROUP BY c.country_iso3, c.country_name;

CREATE VIEW IF NOT EXISTS agg_exchange_rate_monthly AS
SELECT
    b.currency_code AS base_code,
    q.currency_code AS currency,
    d.year,
    d.month,
    AVG(f.rate) AS avg_rate,
    MIN(f.rate) AS min_rate,
    MAX(f.rate) AS max_rate,
    COUNT(*) AS days_observed
FROM fact_exchange_rate f
JOIN dim_currency b ON b.currency_key = f.base_currency_key
JOIN dim_currency q ON q.currency_key = f.quote_currency_key
JOIN dim_date d USING (date_key)
GROUP BY b.currency_code, q.currency_code, d.year, d.month;

CREATE VIEW IF NOT EXISTS agg_crypto_monthly AS
SELECT
    c.coin_id,
    c.symbol,
    c.name,
    d.year,
    d.month,
    AVG(f.price_usd) AS avg_price_usd,
    AVG(f.volume_usd) AS avg_volume_usd,
    AVG(f.price_change_pct_24h) AS avg_price_change_pct_24h,
    COUNT(*) AS days_observed
FROM fact_crypto f
JOIN dim_coin c USING (coin_key)
JOIN dim_date d USING (date_key)
GROUP BY c.coin_id, c.symbol, c.name, d.year, d.month;

CREATE VIEW IF NOT EXISTS agg_weather_monthly AS
SELECT
    l.latitude,
    l.longitude,
    d.year,
    d.month,
    AVG(f.temp_max_c) AS avg_temp_max_c,
    AVG(f.temp_min_c) AS avg_temp_min_c,
    SUM(f.precipitation_mm) AS total_precipitation_mm,
    COUNT(*) AS days_observed
FROM fact_weather f
JOIN dim_location l USING (location_key)
JOIN dim_date d USING (date_key)
GROUP BY l.latitude, l.longitude, d.year, d.month;
