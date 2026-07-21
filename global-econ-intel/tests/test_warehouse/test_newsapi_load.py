from __future__ import annotations

import pandas as pd


def _silver() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_name": ["Reuters", None],  # second article has no source name
            "author": ["Jane Doe", None],
            "title": ["Markets rally", "Op-ed on trade"],
            "description": ["...", None],
            "url": ["https://ex.com/a", "https://ex.com/b"],
            "published_at": ["2026-07-20T09:00:00Z", "2026-07-20T11:30:00Z"],
            "articles_that_day": [2, 2],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )


def test_only_named_sources_become_dimension_members(loader):
    loader.load_newsapi(_silver())

    sources = [r[0] for r in loader.con.execute("SELECT source_name FROM dim_news_source").fetchall()]
    assert sources == ["Reuters"]  # the null-source article did not invent a member


def test_sourceless_article_still_loads_with_null_key(loader):
    loader.load_newsapi(_silver())

    both = loader.con.execute(
        "SELECT url, news_source_key FROM fact_news ORDER BY url"
    ).fetchall()
    assert both[0][1] is not None            # https://ex.com/a -> Reuters
    assert both[1] == ("https://ex.com/b", None)  # sourceless, but the fact is kept


def test_dedupes_on_url_across_reruns(loader):
    loader.load_newsapi(_silver())

    rerun = _silver()
    rerun.loc[rerun["url"] == "https://ex.com/a", "title"] = "Markets rally (updated)"
    loader.load_newsapi(rerun)

    assert loader.con.execute("SELECT count(*) FROM fact_news").fetchone()[0] == 2
    title = loader.con.execute(
        "SELECT title FROM fact_news WHERE url = 'https://ex.com/a'"
    ).fetchone()[0]
    assert title == "Markets rally (updated)"
