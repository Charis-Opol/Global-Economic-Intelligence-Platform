# Superset dashboard definitions (Day 3, Step 5)

Declarative "config as code" for the six example dashboards (GDP, Inflation,
Weather, Crypto, Exchange, Forecasts), in Superset's own export/import YAML
format - the same directory structure `superset export-assets` produces and
`superset import-assets` (or the `/api/v1/assets/import/` REST endpoint)
consumes.

**These were authored without a live Superset instance to validate against.**
There was no running Superset in the environment this was built in to click
through and confirm the import succeeds byte-for-byte - Superset's exact YAML
schema (chart `params`/`query_context` JSON shape especially) has shifted
across versions, so treat this as a strong starting point, not a guarantee.
Before relying on it:

1. Bring up the stack (`docker compose up -d --build superset-init superset`)
   and confirm Superset itself boots clean.
2. Import: `docker compose exec superset superset import-assets --path /app/dashboards`
   (mount this directory into the container, or copy it in - see the
   commented volume line in `docker-compose.yml`'s superset service).
3. Open each dashboard once in the regular Superset UI and confirm its chart
   actually renders against real warehouse data - an import that succeeds
   without error does not guarantee every chart's query is meaningful.
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
databases/duckdb_warehouse.yaml   - the one DuckDB connection every dataset uses
datasets/*.yaml                   - one per domain, pointing at a warehouse view
charts/*.yaml                     - one simple chart per dataset
dashboards/*.yaml                 - one dashboard per domain, wrapping its chart
metadata.yaml                     - required top-level manifest for the import
```

`dashboards/forecasts.yaml` is deliberately chart-less - a markdown panel
pointing at the app's own **/predictions** page instead. There's no
warehouse table of historical forecast outputs to chart (predictions are
computed live from the MLflow champion model against the latest feature
row), so a real chart here would mean fabricating data or adding a
prediction-logging table that was never asked for - out of scope for this
milestone.
