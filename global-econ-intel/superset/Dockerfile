FROM apache/superset:latest

USER root
# Superset itself runs from /app/.venv (confirmed via its own tracebacks
# referencing /app/.venv/lib/.../site-packages) - but that venv has no pip
# binary or pip module at all (a stripped-down production venv), so
# `/app/.venv/bin/pip install` isn't an option. The system pip (at
# /usr/local/bin, a separate Python entirely) has a `--python <path>` flag
# that's *supposed* to install into a different interpreter's site-packages,
# but verified empirically that it actually installs into the SYSTEM
# site-packages instead when the target venv has no pip of its own to
# introspect against - invisible to the venv Superset actually runs from.
# `--target` pointed directly at the venv's site-packages directory is the
# fix that actually works: verified it lands duckdb/duckdb-engine/psycopg2
# there, and it correctly skips (doesn't overwrite) packages Superset's own
# venv already bundles (sqlalchemy, greenlet, packaging, typing_extensions),
# avoiding a version mismatch against what Superset's own code expects.
#
# duckdb pinned to match the version that actually writes warehouse.duckdb
# (pipelines/warehouse) - DuckDB's file format isn't always readable across
# versions, so these two must stay in lockstep. psycopg2-binary is the
# Postgres driver - not bundled by default since Superset supports several
# database backends and doesn't assume Postgres.
RUN pip install --no-cache-dir --target /app/.venv/lib/python3.10/site-packages \
    duckdb==1.5.4 duckdb-engine==0.17.0 psycopg2-binary==2.9.9

# Already on the base image's PYTHONPATH - Superset auto-loads
# superset_config.py from here, no SUPERSET_CONFIG_PATH env var needed.
COPY superset_config.py /app/pythonpath/superset_config.py

# Run once by superset-init after `superset init` - see docker-compose.yml
# and this script's own docstring for why it's needed.
COPY grant_public_role.py /app/grant_public_role.py

USER superset
