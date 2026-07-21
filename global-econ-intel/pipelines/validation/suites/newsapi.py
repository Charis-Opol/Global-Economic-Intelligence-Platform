"""Great Expectations suite for the NewsAPI Silver dataset (Day 1, Step 9)."""
from __future__ import annotations

import great_expectations as gx
from great_expectations import expectations as gxe

COLUMNS = [
    "source_name",
    "author",
    "title",
    "description",
    "url",
    "published_at",
    "articles_that_day",
    "logical_date",
]


def build_suite() -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="newsapi_silver")

    suite.add_expectation(gxe.ExpectTableColumnsToMatchSet(column_set=COLUMNS))

    # Nulls - author/description/source_name are legitimately optional
    # (NewsAPI doesn't always supply them); title/url are the article's identity.
    for column in ["title", "url", "logical_date"]:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    # Duplicates: one row per article URL.
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="url"))

    # Ranges
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="articles_that_day", min_value=1, max_value=None)
    )

    return suite
