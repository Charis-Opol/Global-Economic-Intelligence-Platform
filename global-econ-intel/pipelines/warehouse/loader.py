"""
Load validated Silver datasets into the DuckDB star schema (Day 1, Step 10).

Each `load_*` method takes a Silver `pandas.DataFrame` (exactly what the Step 8
Spark jobs write and the Step 9 validator reads) and upserts it into the star
schema in two moves:

  1. Upsert this source's dimension rows, keyed by their natural key. A rerun
     re-inserts the same natural keys, and ``ON CONFLICT`` collapses them onto
     the existing surrogate key - no duplicate dimension members.
  2. Insert the fact rows, resolving each natural key to its surrogate key with
     a join, and ``ON CONFLICT`` on the fact's grain so a rerun overwrites the
     measures for that grain instead of duplicating them.

Both halves are idempotent, so loading the same Silver dataset twice leaves the
warehouse identical - the same idempotency guarantee the Bronze writer and the
Spark merge step already provide upstream.

The DataFrame is registered as a DuckDB view named ``silver_df``; all the work
happens in SQL against it, so there is no row-by-row Python in the hot path.
"""
from __future__ import annotations

import logging

import duckdb
import pandas as pd

logger = logging.getLogger("pipelines.warehouse")

# DuckDB expression turning a DATE-castable column into a YYYYMMDD int date_key.
# Kept as one definition so the dim_date load and every fact join agree exactly.
_DATE_KEY = "CAST(strftime(CAST({col} AS DATE), '%Y%m%d') AS INTEGER)"


class WarehouseLoader:
    """Loads Silver DataFrames into an already-created star schema.

    The connection is expected to have had `create_schema` applied to it
    already (the CLI does this; tests do it explicitly).
    """

    def __init__(self, con: duckdb.DuckDBPyConnection) -> None:
        self.con = con

    def load(self, source: str, df: pd.DataFrame) -> None:
        """Dispatch to the loader for `source` (one of `LOADERS`)."""
        if source not in LOADERS:
            raise ValueError(f"Unknown source '{source}'. Known: {sorted(LOADERS)}")
        LOADERS[source](self, df)

    # -- shared helpers ------------------------------------------------------

    def _load_dim_date(self, date_col: str) -> None:
        """Populate `dim_date` from the distinct dates in `silver_df.<date_col>`.

        Called before each daily fact load so every `date_key` a fact
        references already exists in the dimension.
        """
        self.con.execute(
            f"""
            INSERT INTO dim_date
            SELECT
                {_DATE_KEY.format(col='d')} AS date_key,
                d            AS full_date,
                year(d)      AS year,
                quarter(d)   AS quarter,
                month(d)     AS month,
                monthname(d) AS month_name,
                day(d)       AS day,
                dayofweek(d) AS day_of_week,
                dayname(d)   AS day_name,
                dayofweek(d) IN (0, 6) AS is_weekend
            FROM (
                SELECT DISTINCT CAST({date_col} AS DATE) AS d
                FROM silver_df
                WHERE {date_col} IS NOT NULL
            )
            ON CONFLICT (date_key) DO NOTHING
            """
        )

    # -- per-source loaders --------------------------------------------------

    def load_world_bank(self, df: pd.DataFrame) -> None:
        self.con.register("silver_df", df)
        try:
            self.con.execute(
                """
                INSERT INTO dim_country (country_iso3, country_name)
                SELECT country_iso3, any_value(country_name)
                FROM silver_df
                WHERE country_iso3 IS NOT NULL
                GROUP BY country_iso3
                ON CONFLICT (country_iso3)
                    DO UPDATE SET country_name = excluded.country_name
                """
            )
            self.con.execute(
                """
                INSERT INTO fact_gdp
                    (country_key, indicator_id, year, gdp_usd, gdp_growth_rate)
                SELECT c.country_key, s.indicator_id, CAST(s.year AS INTEGER),
                       s.gdp_usd, s.gdp_growth_rate
                FROM silver_df s
                JOIN dim_country c ON c.country_iso3 = s.country_iso3
                ON CONFLICT (country_key, indicator_id, year) DO UPDATE SET
                    gdp_usd         = excluded.gdp_usd,
                    gdp_growth_rate = excluded.gdp_growth_rate
                """
            )
        finally:
            self.con.unregister("silver_df")
        logger.info("world_bank: loaded %d silver rows into fact_gdp", len(df))

    def load_world_bank_inflation(self, df: pd.DataFrame) -> None:
        self.con.register("silver_df", df)
        try:
            self.con.execute(
                """
                INSERT INTO dim_country (country_iso3, country_name)
                SELECT country_iso3, any_value(country_name)
                FROM silver_df
                WHERE country_iso3 IS NOT NULL
                GROUP BY country_iso3
                ON CONFLICT (country_iso3)
                    DO UPDATE SET country_name = excluded.country_name
                """
            )
            self.con.execute(
                """
                INSERT INTO fact_inflation
                    (country_key, indicator_id, year, inflation_pct, inflation_trend)
                SELECT c.country_key, s.indicator_id, CAST(s.year AS INTEGER),
                       s.inflation_pct, s.inflation_trend
                FROM silver_df s
                JOIN dim_country c ON c.country_iso3 = s.country_iso3
                ON CONFLICT (country_key, indicator_id, year) DO UPDATE SET
                    inflation_pct   = excluded.inflation_pct,
                    inflation_trend = excluded.inflation_trend
                """
            )
        finally:
            self.con.unregister("silver_df")
        logger.info("world_bank_inflation: loaded %d silver rows into fact_inflation", len(df))

    def load_exchange_rate(self, df: pd.DataFrame) -> None:
        self.con.register("silver_df", df)
        try:
            # A currency can appear as a base or a quote - union both sides
            # into the one conformed dimension.
            self.con.execute(
                """
                INSERT INTO dim_currency (currency_code)
                SELECT DISTINCT code FROM (
                    SELECT base_code AS code FROM silver_df
                    UNION
                    SELECT currency  AS code FROM silver_df
                )
                WHERE code IS NOT NULL
                ON CONFLICT (currency_code) DO NOTHING
                """
            )
            self._load_dim_date("logical_date")
            self.con.execute(
                f"""
                INSERT INTO fact_exchange_rate
                    (base_currency_key, quote_currency_key, date_key,
                     rate, exchange_momentum)
                SELECT b.currency_key, q.currency_key,
                       {_DATE_KEY.format(col='s.logical_date')},
                       s.rate, s.exchange_momentum
                FROM silver_df s
                JOIN dim_currency b ON b.currency_code = s.base_code
                JOIN dim_currency q ON q.currency_code = s.currency
                ON CONFLICT (base_currency_key, quote_currency_key, date_key)
                    DO UPDATE SET
                        rate              = excluded.rate,
                        exchange_momentum = excluded.exchange_momentum
                """
            )
        finally:
            self.con.unregister("silver_df")
        logger.info("exchange_rate: loaded %d silver rows into fact_exchange_rate", len(df))

    def load_open_meteo(self, df: pd.DataFrame) -> None:
        self.con.register("silver_df", df)
        try:
            self.con.execute(
                """
                INSERT INTO dim_location (latitude, longitude)
                SELECT DISTINCT latitude, longitude
                FROM silver_df
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                ON CONFLICT (latitude, longitude) DO NOTHING
                """
            )
            self._load_dim_date("date")
            self.con.execute(
                f"""
                INSERT INTO fact_weather
                    (location_key, date_key, temp_max_c, temp_min_c,
                     precipitation_mm, precip_30d_avg_mm, rainfall_anomaly_mm)
                SELECT l.location_key, {_DATE_KEY.format(col='s.date')},
                       s.temp_max_c, s.temp_min_c, s.precipitation_mm,
                       s.precip_30d_avg_mm, s.rainfall_anomaly_mm
                FROM silver_df s
                JOIN dim_location l
                    ON l.latitude = s.latitude AND l.longitude = s.longitude
                ON CONFLICT (location_key, date_key) DO UPDATE SET
                    temp_max_c          = excluded.temp_max_c,
                    temp_min_c          = excluded.temp_min_c,
                    precipitation_mm    = excluded.precipitation_mm,
                    precip_30d_avg_mm   = excluded.precip_30d_avg_mm,
                    rainfall_anomaly_mm = excluded.rainfall_anomaly_mm
                """
            )
        finally:
            self.con.unregister("silver_df")
        logger.info("open_meteo: loaded %d silver rows into fact_weather", len(df))

    def load_coingecko(self, df: pd.DataFrame) -> None:
        self.con.register("silver_df", df)
        try:
            self.con.execute(
                """
                INSERT INTO dim_coin (coin_id, symbol, name)
                SELECT coin_id, any_value(symbol), any_value(name)
                FROM silver_df
                WHERE coin_id IS NOT NULL
                GROUP BY coin_id
                ON CONFLICT (coin_id) DO UPDATE SET
                    symbol = excluded.symbol,
                    name   = excluded.name
                """
            )
            self._load_dim_date("logical_date")
            self.con.execute(
                f"""
                INSERT INTO fact_crypto
                    (coin_key, date_key, price_usd, market_cap_usd, volume_usd,
                     price_change_pct_24h, volatility_7d)
                SELECT c.coin_key, {_DATE_KEY.format(col='s.logical_date')},
                       s.price_usd, s.market_cap_usd, s.volume_usd,
                       s.price_change_pct_24h, s.volatility_7d
                FROM silver_df s
                JOIN dim_coin c ON c.coin_id = s.coin_id
                ON CONFLICT (coin_key, date_key) DO UPDATE SET
                    price_usd            = excluded.price_usd,
                    market_cap_usd       = excluded.market_cap_usd,
                    volume_usd           = excluded.volume_usd,
                    price_change_pct_24h = excluded.price_change_pct_24h,
                    volatility_7d        = excluded.volatility_7d
                """
            )
        finally:
            self.con.unregister("silver_df")
        logger.info("coingecko: loaded %d silver rows into fact_crypto", len(df))

    def load_newsapi(self, df: pd.DataFrame) -> None:
        self.con.register("silver_df", df)
        try:
            self.con.execute(
                """
                INSERT INTO dim_news_source (source_name)
                SELECT DISTINCT source_name
                FROM silver_df
                WHERE source_name IS NOT NULL
                ON CONFLICT (source_name) DO NOTHING
                """
            )
            self._load_dim_date("logical_date")
            # LEFT JOIN: an article with no source name still loads, with a
            # null news_source_key - we drop the source member, not the fact.
            self.con.execute(
                f"""
                INSERT INTO fact_news
                    (url, news_source_key, date_key, title, author,
                     description, published_at, articles_that_day)
                SELECT s.url, ns.news_source_key,
                       {_DATE_KEY.format(col='s.logical_date')},
                       s.title, s.author, s.description,
                       CAST(s.published_at AS TIMESTAMP), s.articles_that_day
                FROM silver_df s
                LEFT JOIN dim_news_source ns ON ns.source_name = s.source_name
                ON CONFLICT (url) DO UPDATE SET
                    news_source_key   = excluded.news_source_key,
                    date_key          = excluded.date_key,
                    title             = excluded.title,
                    author            = excluded.author,
                    description       = excluded.description,
                    published_at      = excluded.published_at,
                    articles_that_day = excluded.articles_that_day
                """
            )
        finally:
            self.con.unregister("silver_df")
        logger.info("newsapi: loaded %d silver rows into fact_news", len(df))


# Source name -> loader method, mirroring `pipelines.validation.SUITE_BUILDERS`
# so the CLI can offer the same `--source` choices the validator does.
LOADERS = {
    "world_bank": WarehouseLoader.load_world_bank,
    "world_bank_inflation": WarehouseLoader.load_world_bank_inflation,
    "exchange_rate": WarehouseLoader.load_exchange_rate,
    "open_meteo": WarehouseLoader.load_open_meteo,
    "coingecko": WarehouseLoader.load_coingecko,
    "newsapi": WarehouseLoader.load_newsapi,
}
