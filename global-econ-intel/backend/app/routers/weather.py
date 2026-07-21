"""Weather domain endpoint (Day 2, Steps 1 & 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app import repository
from app.db import get_connection
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
    return repository.list_weather(
        con,
        latitude=latitude,
        longitude=longitude,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
