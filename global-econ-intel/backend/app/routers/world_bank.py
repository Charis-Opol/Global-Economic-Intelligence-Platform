"""World Bank domain endpoints: countries and GDP (Day 2, Step 6)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db import fetch_rows, fetch_scalar, get_connection, where_clause
from app.schemas import Country, GDPRecord, Page

router = APIRouter(tags=["world-bank"])


@router.get("/countries", response_model=Page[Country])
def list_countries(
    con=Depends(get_connection),
    search: Annotated[str | None, Query(description="Substring match on ISO3 code or country name")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    clauses, params = [], []
    if search:
        clauses.append("(country_iso3 ILIKE ? OR country_name ILIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where = where_clause(clauses)

    total = fetch_scalar(con, f"SELECT count(*) FROM dim_country {where}", params)
    rows = fetch_rows(
        con,
        f"SELECT country_iso3, country_name FROM dim_country {where} "
        "ORDER BY country_iso3 LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


@router.get("/gdp", response_model=Page[GDPRecord])
def list_gdp(
    con=Depends(get_connection),
    country: Annotated[str | None, Query(description="ISO3 country code, e.g. UGA")] = None,
    indicator_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    clauses, params = [], []
    if country:
        clauses.append("c.country_iso3 = ?")
        params.append(country.upper())
    if indicator_id:
        clauses.append("f.indicator_id = ?")
        params.append(indicator_id)
    if year_min is not None:
        clauses.append("f.year >= ?")
        params.append(year_min)
    if year_max is not None:
        clauses.append("f.year <= ?")
        params.append(year_max)
    where = where_clause(clauses)

    base_sql = f"""
        FROM fact_gdp f
        JOIN dim_country c USING (country_key)
        {where}
    """
    total = fetch_scalar(con, f"SELECT count(*) {base_sql}", params)
    rows = fetch_rows(
        con,
        f"""
        SELECT c.country_iso3, c.country_name, f.indicator_id, f.year,
               f.gdp_usd, f.gdp_growth_rate
        {base_sql}
        ORDER BY c.country_iso3, f.year
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    return {"items": rows, "total": total, "limit": limit, "offset": offset}
