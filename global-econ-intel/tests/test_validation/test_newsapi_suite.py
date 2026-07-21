from __future__ import annotations

import pandas as pd

from pipelines.validation.runner import validate_dataframe
from pipelines.validation.suites.newsapi import build_suite


def test_valid_data_passes():
    df = pd.DataFrame(
        {
            "source_name": ["Reuters", "BBC"],
            "author": ["Jane Doe", None],
            "title": ["Inflation eases", "GDP grows"],
            "description": ["A short summary.", None],
            "url": ["https://example.com/a", "https://example.com/b"],
            "published_at": ["2026-07-20T08:00:00", "2026-07-20T09:00:00"],
            "articles_that_day": [2, 2],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="newsapi")
    assert outcome.success


def test_catches_duplicate_url_and_missing_title():
    df = pd.DataFrame(
        {
            "source_name": ["Reuters", "Reuters", "BBC"],
            "author": ["Jane Doe", "Jane Doe", None],
            "title": ["Inflation eases", "Inflation eases", None],  # missing title
            "description": ["A short summary.", "A short summary.", None],
            "url": ["https://example.com/a", "https://example.com/a", "https://example.com/c"],  # dup URL
            "published_at": ["2026-07-20T08:00:00", "2026-07-20T08:00:00", "2026-07-20T09:00:00"],
            "articles_that_day": [3, 3, 3],
            "logical_date": ["2026-07-20", "2026-07-20", "2026-07-20"],
        }
    )
    outcome = validate_dataframe(df, build_suite, asset_name="newsapi")

    assert not outcome.success
    assert "expect_column_values_to_not_be_null" in outcome.failed_expectations
    assert "expect_column_values_to_be_unique" in outcome.failed_expectations
