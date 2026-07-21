"""Exchange rate: Bronze -> Silver transform (Day 1, Step 8)."""
from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def transform(bronze_df: DataFrame) -> DataFrame:
    """
    bronze_df: one row per ingested bronze document; each page has a
    `base_code` and a `rates` map of currency -> rate.

    Produces one row per (base_code, currency, day) with a day-over-day
    momentum feature.
    """
    pages = bronze_df.select("logical_date", "fetched_at", F.explode("pages").alias("page"))

    # Spark's JSON schema inference treats an object with dynamic keys
    # (currency codes) as a STRUCT, not a MAP - the field set depends on
    # which currencies happened to be in that particular response. This
    # round-trip normalizes it to a real map regardless of how it was
    # inferred, so `explode` works reliably either way.
    with_rates_map = pages.withColumn(
        "rates_map", F.from_json(F.to_json(F.col("page.rates")), "map<string,double>")
    )

    exploded = with_rates_map.select(
        "logical_date",
        "fetched_at",
        F.col("page.base_code").alias("base_code"),
        F.explode(F.col("rates_map")).alias("currency", "rate"),
    )

    cleaned = exploded.filter(F.col("rate") > 0)

    # Merge: dedupe same-day reruns, keeping the most recently fetched rate.
    key_cols = ["base_code", "currency", "logical_date"]
    window = Window.partitionBy(*key_cols).orderBy(F.col("fetched_at").desc())
    deduped = (
        cleaned.withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    # Feature: day-over-day rate momentum per currency pair.
    momentum_window = Window.partitionBy("base_code", "currency").orderBy("logical_date")
    with_features = deduped.withColumn(
        "prior_rate", F.lag("rate").over(momentum_window)
    ).withColumn(
        "exchange_momentum",
        F.when(
            F.col("prior_rate").isNotNull() & (F.col("prior_rate") != 0),
            (F.col("rate") - F.col("prior_rate")) / F.col("prior_rate"),
        ).otherwise(F.lit(None).cast("double")),
    )

    return with_features.select(
        "base_code", "currency", "rate", "exchange_momentum", "logical_date"
    )
