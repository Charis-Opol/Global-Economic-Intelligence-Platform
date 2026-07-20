from __future__ import annotations

import pytest

from pipelines.connectors.exceptions import ConnectorRequestError
from pipelines.connectors.newsapi import NewsAPIConnector
from tests.test_connectors.conftest import FakeResponse


def _article(title: str) -> dict:
    return {
        "source": {"id": None, "name": "Reuters"},
        "author": "Jane Doe",
        "title": title,
        "description": "A short summary.",
        "url": "https://example.com/article",
        "publishedAt": "2026-07-20T00:00:00Z",
    }


def test_missing_api_key_raises_without_network_call():
    connector = NewsAPIConnector(api_key="")

    with pytest.raises(ConnectorRequestError):
        connector.fetch_one()


def test_fetch_with_api_key(patch_session_get):
    calls = patch_session_get(
        [
            FakeResponse(
                {"status": "ok", "totalResults": 1, "articles": [_article("Inflation eases")]}
            )
        ]
    )
    connector = NewsAPIConnector(api_key="test-key")

    result = connector.fetch_one()

    assert result.articles[0].title == "Inflation eases"
    assert calls[0]["params"]["apiKey"] == "test-key"


def test_free_tier_page_cap_stops_pagination(patch_session_get):
    # Even though totalResults implies more pages exist, the free tier
    # can't actually retrieve them, so pagination must stop at max_pages.
    patch_session_get(
        [
            FakeResponse(
                {"status": "ok", "totalResults": 500, "articles": [_article("Story 1")]}
            )
        ]
    )
    connector = NewsAPIConnector(api_key="test-key")

    pages = list(connector.fetch_all())

    assert len(pages) == 1
