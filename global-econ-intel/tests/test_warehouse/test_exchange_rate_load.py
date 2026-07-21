from __future__ import annotations

import pandas as pd


def _silver() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "base_code": ["USD", "USD"],
            "currency": ["UGX", "EUR"],
            "rate": [3700.5, 0.92],
            "exchange_momentum": [0.01, None],
            "logical_date": ["2026-07-20", "2026-07-20"],
        }
    )


def test_currencies_are_conformed_across_base_and_quote(loader):
    loader.load_exchange_rate(_silver())

    # USD (a base) and UGX/EUR (quotes) all land in the one currency dimension.
    codes = [
        r[0]
        for r in loader.con.execute(
            "SELECT currency_code FROM dim_currency ORDER BY currency_code"
        ).fetchall()
    ]
    assert codes == ["EUR", "UGX", "USD"]


def test_facts_resolve_both_currency_keys_and_the_date(loader):
    loader.load_exchange_rate(_silver())

    rows = loader.con.execute(
        """
        SELECT b.currency_code, q.currency_code, d.full_date, f.rate
        FROM fact_exchange_rate f
        JOIN dim_currency b ON b.currency_key = f.base_currency_key
        JOIN dim_currency q ON q.currency_key = f.quote_currency_key
        JOIN dim_date d USING (date_key)
        ORDER BY q.currency_code
        """
    ).fetchall()
    assert rows == [
        ("USD", "EUR", pd.Timestamp("2026-07-20").date(), 0.92),
        ("USD", "UGX", pd.Timestamp("2026-07-20").date(), 3700.5),
    ]


def test_rerun_overwrites_rate_for_the_same_pair_and_day(loader):
    loader.load_exchange_rate(_silver())

    later = _silver()
    later.loc[later["currency"] == "UGX", "rate"] = 3750.0
    loader.load_exchange_rate(later)

    assert loader.con.execute("SELECT count(*) FROM fact_exchange_rate").fetchone()[0] == 2
    ugx = loader.con.execute(
        """
        SELECT f.rate FROM fact_exchange_rate f
        JOIN dim_currency q ON q.currency_key = f.quote_currency_key
        WHERE q.currency_code = 'UGX'
        """
    ).fetchone()[0]
    assert ugx == 3750.0
