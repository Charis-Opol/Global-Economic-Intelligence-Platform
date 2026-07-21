"""News domain endpoint (Day 2, Step 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db import fetch_rows, fetch_scalar, get_connection, where_clause
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
    clauses, params = [], []
    if source:
        clauses.append("ns.source_name = ?")
        params.append(source)
    if date_from:
        clauses.append("d.full_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("d.full_date <= ?")
        params.append(date_to)
    if q:
        clauses.append("f.title ILIKE ?")
        params.append(f"%{q}%")
    where = where_clause(clauses)

    # LEFT JOIN dim_news_source: an article can legitimately have no source
    # name (Step 10 loads it with a null news_source_key rather than
    # inventing a dimension member), so it must not be dropped by a JOIN here.
    base_sql = f"""
        FROM fact_news f
        LEFT JOIN dim_news_source ns USING (news_source_key)
        JOIN dim_date d USING (date_key)
        {where}
    """
    total = fetch_scalar(con, f"SELECT count(*) {base_sql}", params)
    rows = fetch_rows(
        con,
        f"""
        SELECT f.url, ns.source_name, f.title, f.author, f.description,
               f.published_at, d.full_date AS date, f.articles_that_day
        {base_sql}
        ORDER BY d.full_date DESC, f.url
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}
