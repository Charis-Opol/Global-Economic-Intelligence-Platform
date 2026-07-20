"""
NewsAPI connector.

Docs: https://newsapi.org/docs/endpoints/everything

Requires an API key (NEWSAPI_KEY - see .env.example). Paginated via
`page`/`pageSize`; capped at `max_pages` since the free tier only
returns the first 100 results regardless of `totalResults`.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from config.settings import shared_settings
from pipelines.connectors.base import BaseConnector
from pipelines.connectors.exceptions import ConnectorRequestError


class NewsSource(BaseModel):
    id: str | None = None
    name: str


class NewsArticle(BaseModel):
    source: NewsSource
    author: str | None = None
    title: str
    description: str | None = None
    url: str
    publishedAt: str


class NewsAPIResponse(BaseModel):
    status: str
    totalResults: int
    articles: list[NewsArticle]


class NewsAPIConnector(BaseConnector[NewsAPIResponse]):
    name = "newsapi"
    base_url = "https://newsapi.org/v2"
    page_size = 100
    max_pages = 1  # free tier caps results at 100 total, so page 2+ is empty
    query = "economy OR inflation OR GDP OR central bank"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__()
        self.api_key = api_key or shared_settings.newsapi_key

    @property
    def response_model(self) -> type[NewsAPIResponse]:
        return NewsAPIResponse

    def _request_page(self, page: int) -> Any:
        if not self.api_key:
            raise ConnectorRequestError("NEWSAPI_KEY is not set - check your .env file")
        params = {
            "q": self.query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": self.page_size,
            "page": page,
            "apiKey": self.api_key,
        }
        response = self.session.get(
            f"{self.base_url}/everything", params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def _has_next_page(self, payload: Any, page: int) -> bool:
        total = payload.get("totalResults", 0)
        fetched = page * self.page_size
        return fetched < total and page < self.max_pages
