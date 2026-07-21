"""NewsAPI: Bronze -> Silver transform (Day 1, Step 8)."""
from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def transform(bronze_df: DataFrame) -> DataFrame:
    """
    bronze_df: one row per ingested bronze document; each page has an
    `articles` array.

    Produces one row per article, deduped by URL, plus a same-day
    article-count feature - a simple news-volume signal for later models.
    """
    pages = bronze_df.select("logical_date", "fetched_at", F.explode("pages").alias("page"))
    articles = pages.select(
        "logical_date", "fetched_at", F.explode("page.articles").alias("article")
    )

    flat = articles.select(
        F.col("article.source.name").alias("source_name"),
        F.col("article.author").alias("author"),
        F.col("article.title").alias("title"),
        F.col("article.description").alias("description"),
        F.col("article.url").alias("url"),
        F.to_timestamp("article.publishedAt").alias("published_at"),
        "logical_date",
        "fetched_at",
    )

    cleaned = flat.filter(F.col("title").isNotNull() & F.col("url").isNotNull())

    # Merge: the same article can appear in more than one day's pull -
    # keep the most recently fetched copy per URL.
    window = Window.partitionBy("url").orderBy(F.col("fetched_at").desc())
    deduped = (
        cleaned.withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

    count_window = Window.partitionBy("logical_date")
    with_features = deduped.withColumn(
        "articles_that_day", F.count("url").over(count_window)
    )

    return with_features.select(
        "source_name",
        "author",
        "title",
        "description",
        "url",
        "published_at",
        "articles_that_day",
        "logical_date",
    )
