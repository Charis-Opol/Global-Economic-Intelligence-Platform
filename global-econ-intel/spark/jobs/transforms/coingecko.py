"""CoinGecko crypto: Bronze -> Silver transform (Day 1, Step 8)."""
from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def transform(bronze_df: DataFrame) -> DataFrame:
    """
    bronze_df: one row per ingested bronze document; each page has a
    `coins` array (id, symbol, name, current_price, market_cap,
    total_volume, price_change_percentage_24h).

    Produces one row per (coin_id, day) with a trailing 7-day volatility
    feature (stddev of the 24h price-change percentage).
    """
    pages = bronze_df.select("logical_date", "fetched_at", F.explode("pages").alias("page"))
    coins = pages.select("logical_date", "fetched_at", F.explode("page.coins").alias("coin"))

    flat = coins.select(
        F.col("coin.id").alias("coin_id"),
        F.col("coin.symbol").alias("symbol"),
        F.col("coin.name").alias("name"),
        F.col("coin.current_price").cast("double").alias("price_usd"),
        F.col("coin.market_cap").cast("double").alias("market_cap_usd"),
        F.col("coin.total_volume").cast("double").alias("volume_usd"),
        F.col("coin.price_change_percentage_24h").cast("double").alias("price_change_pct_24h"),
        "logical_date",
        "fetched_at",
    )

    cleaned = flat.filter(F.col("coin_id").isNotNull() & F.col("price_usd").isNotNull())

    # Merge: dedupe same-day reruns, keeping the most recently fetched snapshot.
    key_cols = ["coin_id", "logical_date"]
    window = Window.partitionBy(*key_cols).orderBy(F.col("fetched_at").desc())
    deduped = (
        cleaned.withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    # Feature: trailing 7-day volatility per coin.
    volatility_window = Window.partitionBy("coin_id").orderBy("logical_date").rowsBetween(-6, 0)
    with_features = deduped.withColumn(
        "volatility_7d", F.stddev("price_change_pct_24h").over(volatility_window)
    )

    return with_features.select(
        "coin_id",
        "symbol",
        "name",
        "price_usd",
        "market_cap_usd",
        "volume_usd",
        "price_change_pct_24h",
        "volatility_7d",
        "logical_date",
    )
