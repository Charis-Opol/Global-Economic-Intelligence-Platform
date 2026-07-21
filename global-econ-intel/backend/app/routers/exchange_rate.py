"""Exchange rate domain endpoint (Day 2, Steps 1 & 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app import repository
from app.db import get_connection
from app.schemas import ExchangeRate, Page

router = APIRouter(tags=["exchange-rate"])


@router.get("/exchange", response_model=Page[ExchangeRate])
def list_exchange_rates(
    con=Depends(get_connection),
    base: Annotated[str | None, Query(description="Base currency code, e.g. USD")] = None,
    quote: Annotated[str | None, Query(description="Quote currency code, e.g. EUR")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return repository.list_exchange_rates(
        con, base=base, quote=quote, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
