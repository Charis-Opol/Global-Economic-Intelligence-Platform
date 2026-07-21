from __future__ import annotations


def test_sourceless_article_is_still_returned(client):
    resp = client.get("/news", params={"q": "op-ed"})
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["source_name"] is None
    assert body["items"][0]["url"] == "https://ex.com/b"


def test_filter_by_source_excludes_the_sourceless_article(client):
    resp = client.get("/news", params={"source": "Reuters"})
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://ex.com/a"


def test_no_filters_returns_both_articles(client):
    resp = client.get("/news")
    assert resp.json()["total"] == 2
