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
4. Check the `Public` role (or whatever `GUEST_ROLE_NAME` is set to in
   `superset_config.py`) has "can read on Dashboard" - guest tokens are
   scoped to a role, and Superset doesn't grant that automatically.

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
