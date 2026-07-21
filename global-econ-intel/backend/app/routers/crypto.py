"""Crypto domain endpoint (Day 2, Step 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db import fetch_rows, fetch_scalar, get_connection, where_clause
from app.schemas import Crypto, Page

router = APIRouter(tags=["crypto"])


@router.get("/crypto", response_model=Page[Crypto])
def list_crypto(
    con=Depends(get_connection),
    coin_id: Annotated[str | None, Query(description="CoinGecko coin id, e.g. bitcoin")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    clauses, params = [], []
    if coin_id:
        clauses.append("c.coin_id = ?")
        params.append(coin_id.lower())
    if date_from:
        clauses.append("d.full_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("d.full_date <= ?")
        params.append(date_to)
    where = where_clause(clauses)

    base_sql = f"""
        FROM fact_crypto f
        JOIN dim_coin c USING (coin_key)
        JOIN dim_date d USING (date_key)
        {where}
    """
    total = fetch_scalar(con, f"SELECT count(*) {base_sql}", params)
    rows = fetch_rows(
        con,
        f"""
        SELECT c.coin_id, c.symbol, c.name, d.full_date AS date,
               f.price_usd, f.market_cap_usd, f.volume_usd,
               f.price_change_pct_24h, f.volatility_7d
        {base_sql}
        ORDER BY d.full_date, c.coin_id
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}
