"""Weather domain endpoint (Day 2, Step 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db import fetch_rows, fetch_scalar, get_connection, where_clause
from app.schemas import Page, Weather

router = APIRouter(tags=["weather"])


@router.get("/weather", response_model=Page[Weather])
def list_weather(
    con=Depends(get_connection),
    latitude: float | None = None,
    longitude: float | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    clauses, params = [], []
    if latitude is not None:
        clauses.append("l.latitude = ?")
        params.append(latitude)
    if longitude is not None:
        clauses.append("l.longitude = ?")
        params.append(longitude)
    if date_from:
        clauses.append("d.full_date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("d.full_date <= ?")
        params.append(date_to)
    where = where_clause(clauses)

    base_sql = f"""
        FROM fact_weather f
        JOIN dim_location l USING (location_key)
        JOIN dim_date d USING (date_key)
        {where}
    """
    total = fetch_scalar(con, f"SELECT count(*) {base_sql}", params)
    rows = fetch_rows(
        con,
        f"""
        SELECT l.latitude, l.longitude, d.full_date AS date,
               f.temp_max_c, f.temp_min_c, f.precipitation_mm,
               f.precip_30d_avg_mm, f.rainfall_anomaly_mm
        {base_sql}
        ORDER BY d.full_date, l.latitude, l.longitude
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}
