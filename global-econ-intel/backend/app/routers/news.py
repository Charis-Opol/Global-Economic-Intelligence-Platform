"""News domain endpoint (Day 2, Steps 1 & 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app import repository
from app.db import get_connection
from app.schemas import NewsArticle, Page

router = APIRouter(tags=["news"])


@router.get("/news", response_model=Page[NewsArticle])
def list_news(
    con=Depends(get_connection),
    source: Annotated[str | None, Query(description="News source name, e.g. Reuters")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: Annotated[str | None, Query(description="Substring match on the article title")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return repository.list_news(
        con, source=source, date_from=date_from, date_to=date_to, q=q, limit=limit, offset=offset
    )
