# Superset dashboard definitions (Day 3, Step 5)

Declarative "config as code" for the six example dashboards (GDP, Inflation,
Weather, Crypto, Exchange, Forecasts), in Superset's own asset export/import
YAML format - the same directory structure `GET /api/v1/assets/export/`
produces and `POST /api/v1/assets/import/` consumes. There's no
`export-assets`/`import-assets` CLI subcommand on this Superset version (6.1)
- those REST endpoints are the only way in and out.

**Regenerated from a live Superset instance**, not hand-authored: every file
here was produced by actually creating each chart against the running
`duckdb_warehouse` database, confirming its query returns real data, then
exporting the whole asset tree back out and renaming the export's ID-suffixed
filenames (`GDP_Over_Time_Top_10_Economies_6.yaml` etc.) to the clean ones
you see below - filenames are cosmetic, Superset resolves everything by the
`uuid:` field. Round-tripped through a real re-import
(`POST /api/v1/assets/import/`) to confirm the renamed files are still valid
before committing. Still worth doing once after cloning:

1. Bring up the stack (`docker compose up -d --build superset-init superset`)
   and confirm Superset itself boots clean.
2. Import: zip this directory's contents (each file's path relative to a
   single wrapping root folder, forward slashes even on Windows - Superset's
   importer strips the first path component unconditionally) and
   `POST` it as multipart field `bundle` to `/api/v1/assets/import/`.
3. Open each dashboard once in the regular Superset UI and confirm every
   chart actually renders against real warehouse data - an import that
   succeeds without error does not guarantee every chart's query is
   meaningful.
4. The `Public` role (or whatever `GUEST_ROLE_NAME` is set to in
   `superset_config.py`) needs several permissions beyond "can read on
   Dashboard" for an embedded guest session to actually load - the embedded
   iframe's own bootstrap code calls several `/api/v1/*` endpoints (roles,
   charts, explore, ...) before it renders anything, and a 403 on any of
   them surfaces as an opaque "Something went wrong with embedded
   authentication" with no indication of which permission is missing.
   `docker-compose.yml`'s `superset-init` service runs
   `superset/grant_public_role.py` after `superset init` to grant the full
   set automatically - see that script for the exact list and how each entry
   was found. Safe to re-run; only needed manually if you're not going
   through `superset-init` (e.g. importing assets by hand into an
   already-running instance).

Also note: `databases/duckdb_warehouse.yaml`'s `sqlalchemy_uri` has
`?access_mode=READ_ONLY` - required, not optional. `docker-compose.yml`
mounts `./warehouse` at `/opt/warehouse:ro`, and DuckDB opens a file
read-write (acquiring a write lock) by default regardless of query content;
without this every chart query fails with "IO Error: ... Read-only file
system" even though Superset only ever reads through this connection.

Note: enabling *embedding* itself (`POST /api/v1/dashboard/<slug>/embedded`,
which is a separate step from the import above and generates its own uuid
distinct from each dashboard's `uuid:` in these YAML files) is handled
automatically by `backend/app/superset_client.py` the first time a guest
token is requested for a given dashboard - no manual API call needed. See
that file's docstring for why the two uuids are different and why that
distinction matters.

## Layout

```
databases/duckdb_warehouse.yaml     - the one DuckDB connection every dataset uses
datasets/DuckDB_Warehouse/*.yaml    - one per domain, pointing at a warehouse view
                                       (nested by database name - that's what
                                       Superset's own exporter does; not flattened)
charts/*.yaml                       - several per domain (see below)
dashboards/*.yaml                   - one dashboard per domain, stacking its charts
metadata.yaml                       - required top-level manifest for the import
```

Each domain dashboard (GDP, Inflation, Weather, Crypto, Exchange) stacks
multiple chart types, one per row, in this order:

- `*_table.yaml` - the original raw-data table (unchanged from the first cut)
- `*_line.yaml` - a trend over time (or, for GDP/Inflation, over year - see
  below)
- `*_bar.yaml` - a categorical comparison
- `*_map.yaml` (GDP, Inflation only) - a `world_map` choropleth by
  `country_iso3`. Weather and Exchange don't have a real country dimension
  (weather is a single lat/long station, exchange rates are per-currency, and
  a currency isn't a country - EUR alone spans 20) so no choropleth was
  forced onto either.
- `weather_scatter.yaml` (Weather only) - a plain `bubble` chart plotting
  longitude against latitude, sized by temperature. Not a real basemap: the
  deck.gl map chart types Superset ships need a Mapbox access token, and
  Mapbox now requires billing info on file even for its free tier, which
  wasn't available in this environment. This is the keyless fallback -
  accurate relative station positions, no tiles/coastlines underneath. If a
  Mapbox token becomes available later, swap this chart's `viz_type` from
  `bubble_v2` to `deck_scatter` and set `MAPBOX_API_KEY` in `.env`.

GDP and Inflation's `line`/`bar`/`map` charts all exclude World Bank's
regional/income-group aggregate rows (`"World"`, `"OECD members"`,
`"Sub-Saharan Africa"`, ...) via a `NOT LIKE`/`NOT IN` SQL adhoc filter -
the raw `view_gdp`/`view_inflation` datasets mix real countries and these
aggregates in the same `country_name` column with no flag to distinguish
them, and an unfiltered "top N" ranking would otherwise be dominated by
aggregates instead of actual economies. The filter is a best-effort
denylist, not an exhaustive one; see each chart's `adhoc_filters` for the
exact list.

Crypto and Exchange's `line`/`bar` charts filter to a curated set of major
coins/currencies (bitcoin, ethereum, ... / EUR, GBP, ...) rather than
"top N by whatever metric" - both datasets currently hold only a couple of
days of history across hundreds of symbols, so a metric-based ranking would
surface arbitrary illiquid/thin-data symbols rather than anything meaningful.

`dashboards/forecasts.yaml` is deliberately chart-less - a markdown panel
pointing at the app's own **/predictions** page instead. There's no
warehouse table of historical forecast outputs to chart (predictions are
computed live from the MLflow champion model against the latest feature
row), so a real chart here would mean fabricating data or adding a
prediction-logging table that was never asked for - out of scope for this
milestone.
