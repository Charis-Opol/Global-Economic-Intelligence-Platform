"""Open-Meteo weather: Bronze -> Silver transform (Day 1, Step 8)."""
from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def transform(bronze_df: DataFrame) -> DataFrame:
    """
    bronze_df: one row per ingested bronze document; each page has
    latitude/longitude and a `daily` struct of parallel arrays (time,
    temperature_2m_max, temperature_2m_min, precipitation_sum).

    Because each ingestion run re-fetches a rolling window of past_days,
    the same calendar date shows up in multiple bronze documents - the
    merge step below is what keeps this idempotent rather than duplicative.

    Produces one row per calendar day with a 30-day rolling rainfall
    anomaly feature.
    """
    pages = bronze_df.select("logical_date", "fetched_at", F.explode("pages").alias("page"))

    exploded = pages.select(
        "logical_date",
        "fetched_at",
        "page",
        F.posexplode("page.daily.time").alias("pos", "day"),
    )

    daily = exploded.select(
        F.to_date("day").alias("date"),
        F.col("page.latitude").alias("latitude"),
        F.col("page.longitude").alias("longitude"),
        F.col("page.daily.temperature_2m_max")[F.col("pos")].alias("temp_max_c"),
        F.col("page.daily.temperature_2m_min")[F.col("pos")].alias("temp_min_c"),
        F.col("page.daily.precipitation_sum")[F.col("pos")].alias("precipitation_mm"),
        "fetched_at",
        F.col("logical_date"),
    )

    cleaned = daily.filter(F.col("date").isNotNull())

    # Merge: dedupe overlapping days across runs, keeping the most recently fetched.
    window = Window.partitionBy("date").orderBy(F.col("fetched_at").desc())
    deduped = (
        cleaned.withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    # Feature: today's rainfall vs. the trailing 30-day average.
    rolling_window = Window.orderBy("date").rowsBetween(-29, 0)
    with_features = deduped.withColumn(
        "precip_30d_avg_mm", F.avg("precipitation_mm").over(rolling_window)
    ).withColumn(
        "rainfall_anomaly_mm", F.col("precipitation_mm") - F.col("precip_30d_avg_mm")
    )

    return with_features.select(
        "date",
        "latitude",
        "longitude",
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
        "precip_30d_avg_mm",
        "rainfall_anomaly_mm",
        "logical_date",
    )
