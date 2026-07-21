"""World Bank domain endpoints: countries, GDP, and inflation (Day 2, Steps 1 & 6)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app import repository
from app.db import get_connection
from app.schemas import Country, GDPRecord, Inflation, Page

router = APIRouter(tags=["world-bank"])


@router.get("/countries", response_model=Page[Country])
def list_countries(
    con=Depends(get_connection),
    search: Annotated[str | None, Query(description="Substring match on ISO3 code or country name")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return repository.list_countries(con, search=search, limit=limit, offset=offset)


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
    return repository.list_gdp(
        con,
        country=country,
        indicator_id=indicator_id,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
        offset=offset,
    )


@router.get("/inflation", response_model=Page[Inflation])
def list_inflation(
    con=Depends(get_connection),
    country: Annotated[str | None, Query(description="ISO3 country code, e.g. UGA")] = None,
    indicator_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return repository.list_inflation(
        con,
        country=country,
        indicator_id=indicator_id,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
        offset=offset,
    )
