"""World Bank GDP: Bronze -> Silver transform (Day 1, Step 8)."""
from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def transform(bronze_df: DataFrame) -> DataFrame:
    """
    bronze_df: one row per ingested bronze document, with a `pages` array
    of struct<meta, records>.

    Produces one row per (country, indicator, year) with a year-over-year
    GDP growth rate feature.
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
        F.col("record.value").cast("double").alias("gdp_usd"),
        "logical_date",
        "fetched_at",
    )

    # Clean: a real country code and year are required. A null GDP value
    # is a legitimate "not yet reported" data point, so it's kept rather
    # than dropped - Great Expectations (Step 9) flags it, this step doesn't.
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

    # Feature: year-over-year GDP growth rate per country.
    growth_window = Window.partitionBy("country_iso3", "indicator_id").orderBy("year")
    with_growth = deduped.withColumn(
        "prior_year_gdp_usd", F.lag("gdp_usd").over(growth_window)
    ).withColumn(
        "gdp_growth_rate",
        F.when(
            F.col("prior_year_gdp_usd").isNotNull() & (F.col("prior_year_gdp_usd") != 0),
            (F.col("gdp_usd") - F.col("prior_year_gdp_usd")) / F.col("prior_year_gdp_usd"),
        ).otherwise(F.lit(None).cast("double")),
    )

    return with_growth.select(
        "country_iso3",
        "country_name",
        "indicator_id",
        "year",
        "gdp_usd",
        "gdp_growth_rate",
        "logical_date",
    )
