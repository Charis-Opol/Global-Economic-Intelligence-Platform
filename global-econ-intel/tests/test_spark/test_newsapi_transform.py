from __future__ import annotations

from transforms.newsapi import transform


def _article(url: str, title: str, published_at: str, source_name: str = "Reuters") -> dict:
    return {
        "source": {"id": None, "name": source_name},
        "author": "Jane Doe",
        "title": title,
        "description": "A short summary.",
        "url": url,
        "publishedAt": published_at,
    }


def _doc(logical_date: str, fetched_at: str, articles: list[dict]) -> dict:
    return {
        "source": "newsapi",
        "logical_date": logical_date,
        "fetched_at": fetched_at,
        "page_count": 1,
        "pages": [{"status": "ok", "totalResults": len(articles), "articles": articles}],
    }


def test_flattens_articles_into_rows(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        [
            _article("https://example.com/a", "Inflation eases", "2026-07-20T08:00:00Z"),
            _article("https://example.com/b", "GDP grows", "2026-07-20T09:00:00Z"),
        ],
    )
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 2
    assert result[0].articles_that_day == 2


def test_same_article_across_days_dedupes_by_url(make_bronze_df):
    day1 = _doc(
        "2026-07-19T00:00:00+00:00",
        "2026-07-19T01:00:00+00:00",
        [_article("https://example.com/a", "Old headline", "2026-07-19T08:00:00Z")],
    )
    day2 = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        [_article("https://example.com/a", "Updated headline", "2026-07-19T08:00:00Z")],
    )
    result = transform(make_bronze_df([day1, day2])).collect()

    assert len(result) == 1
    assert result[0].title == "Updated headline"


def test_articles_missing_title_or_url_are_dropped(make_bronze_df):
    doc = _doc(
        "2026-07-20T00:00:00+00:00",
        "2026-07-20T01:00:00+00:00",
        [{"source": {"id": None, "name": "Reuters"}, "author": None, "title": None,
          "description": None, "url": "https://example.com/c", "publishedAt": "2026-07-20T08:00:00Z"}],
    )
    result = transform(make_bronze_df([doc])).collect()

    assert len(result) == 0
