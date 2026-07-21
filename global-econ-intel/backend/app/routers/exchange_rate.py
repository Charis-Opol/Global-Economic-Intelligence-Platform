"""Exchange rate domain endpoint (Day 2, Step 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db import fetch_rows, fetch_scalar, get_connection, where_clause
from app.schemas import ExchangeRate, Page

router = APIRouter(tags=["exchange-rate"])


@router.get("/exchange-rates", response_model=Page[ExchangeRate])
def list_exchange_rates(
    con=Depends(get_connection),
    base: Annotated[str | None, Query(description="Base currency code, e.g. USD")] = None,
    quote: Annotated[str | None, Query(description="Quote currency code, e.g. EUR")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    clauses, params = [], []
    if base:
        clauses.append("b.currency_code = ?")
        params.append(base.upper())
    if quote:
        clauses.append("q.currency_code = ?")
        params.append(quote.upper())
    if date_from:
        clauses.append("d.full_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("d.full_date <= ?")
        params.append(date_to)
    where = where_clause(clauses)

    base_sql = f"""
        FROM fact_exchange_rate f
        JOIN dim_currency b ON b.currency_key = f.base_currency_key
        JOIN dim_currency q ON q.currency_key = f.quote_currency_key
        JOIN dim_date d USING (date_key)
        {where}
    """
    total = fetch_scalar(con, f"SELECT count(*) {base_sql}", params)
    rows = fetch_rows(
        con,
        f"""
        SELECT b.currency_code AS base_code, q.currency_code AS currency,
               d.full_date AS date, f.rate, f.exchange_momentum
        {base_sql}
        ORDER BY d.full_date, b.currency_code, q.currency_code
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}
