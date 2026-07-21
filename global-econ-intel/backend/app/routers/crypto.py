"""Crypto domain endpoint (Day 2, Steps 1 & 6)."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app import repository
from app.db import get_connection
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
    return repository.list_crypto(
        con, coin_id=coin_id, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
