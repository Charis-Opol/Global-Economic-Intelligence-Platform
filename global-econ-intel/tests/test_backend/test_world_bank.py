from __future__ import annotations


def test_list_countries_default(client):
    resp = client.get("/countries")
    body = resp.json()

    assert resp.status_code == 200
    assert body["total"] == 2
    assert [c["country_iso3"] for c in body["items"]] == ["KEN", "UGA"]


def test_list_countries_search_filter(client):
    resp = client.get("/countries", params={"search": "uga"})
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["country_iso3"] == "UGA"


def test_list_gdp_filters_by_country_and_year(client):
    resp = client.get("/gdp", params={"country": "uga", "year_min": 2021})
    body = resp.json()

    assert body["total"] == 1
    row = body["items"][0]
    assert row["year"] == 2021
    assert row["gdp_usd"] == 4.0e10
    assert row["country_name"] == "Uganda"


def test_list_gdp_pagination_envelope(client):
    resp = client.get("/gdp", params={"limit": 1})
    body = resp.json()

    assert body["total"] == 3  # total reflects the full match, not the page
    assert len(body["items"]) == 1
    assert body["limit"] == 1
    assert body["offset"] == 0
