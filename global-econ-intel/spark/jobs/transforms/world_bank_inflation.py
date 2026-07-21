"""World Bank inflation: Bronze -> Silver transform (Day 2).

Mirrors transforms/world_bank.py's shape exactly (same API, same bronze
document structure) - the only real difference is the feature: inflation is
already a rate, so "trend" is the year-over-year percentage-point change in
that rate, not a growth rate of a growth rate.
"""
from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def transform(bronze_df: DataFrame) -> DataFrame:
    """
    bronze_df: one row per ingested bronze document, with a `pages` array
    of struct<meta, records>.

    Produces one row per (country, indicator, year) with a year-over-year
    inflation trend feature (percentage-point change from the prior year).
    """
    pages = bronze_df.select("logical_date", "fetched_at", F.explode("pages").alias("page"))
    records = pages.select(
        "logical_date", "fetched_at", F.explode("page.records").alias("record")
    )

    flat = records.select(
        F.col("record.countryiso3code").alias("country_iso3"),
        F.col("record.country.value").alias("country_name"),
        F.col("record.indicator.id").alias("indicator_id"),
        F.col("record.date").cast("int").alias("year"),
        F.col("record.value").cast("double").alias("inflation_pct"),
        "logical_date",
        "fetched_at",
    )

    # Clean: a real country code and year are required. A null inflation
    # value is a legitimate "not yet reported" data point, so it's kept
    # rather than dropped - Great Expectations flags it, this step doesn't.
    cleaned = flat.filter(
        F.col("country_iso3").isNotNull()
        & (F.col("country_iso3") != "")
        & F.col("year").isNotNull()
    )

    # Merge: the same (country, indicator, year) can appear in more than
    # one day's bronze snapshot - keep only the most recently fetched value.
    key_cols = ["country_iso3", "indicator_id", "year"]
    window = Window.partitionBy(*key_cols).orderBy(F.col("fetched_at").desc())
    deduped = (
        cleaned.withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    # Feature: year-over-year change in the inflation rate itself (a
    # percentage-point delta, not a percent-of-percent growth rate).
    trend_window = Window.partitionBy("country_iso3", "indicator_id").orderBy("year")
    with_trend = deduped.withColumn(
        "prior_year_inflation_pct", F.lag("inflation_pct").over(trend_window)
    ).withColumn(
        "inflation_trend",
        F.when(
            F.col("prior_year_inflation_pct").isNotNull(),
            F.col("inflation_pct") - F.col("prior_year_inflation_pct"),
        ).otherwise(F.lit(None).cast("double")),
    )

    return with_trend.select(
        "country_iso3",
        "country_name",
        "indicator_id",
        "year",
        "inflation_pct",
        "inflation_trend",
        "logical_date",
    )
