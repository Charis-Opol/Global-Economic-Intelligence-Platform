"""
Superset config for embedded dashboards (Day 3, Step 5).

Mounted into the stock `apache/superset` image at
`/app/pythonpath/superset_config.py` (already on that image's PYTHONPATH, so
no custom Dockerfile is needed - see docker-compose.yml's superset service).

This file *replaces* the stock image's own default config rather than
layering on top of it - whichever `superset_config.py` is first on
PYTHONPATH wins, and mounting one here means the stock image's own
env-var-driven `SQLALCHEMY_DATABASE_URI` wiring (which normally reads
DATABASE_DIALECT/HOST/DB/USER/PASSWORD) never runs unless this file does it
too. Skipping that the first time this file was written was a real bug -
Superset silently fell back to its own default (a local SQLite file)
instead of the shared Postgres instance every other service uses.

Otherwise everything here is additive to Superset's own defaults - it only
turns on what embedding needs:
  - EMBEDDED_SUPERSET feature flag
  - a guest-token JWT secret (separate from SUPERSET_SECRET_KEY - guest
    tokens are deliberately a different trust boundary)
  - CORS + a frame-ancestors CSP exception, both scoped to the frontend's
    origin specifically, not opened up broadly
"""
import os

# Superset's own default config builds this from the same DATABASE_* env
# vars docker-compose.yml's x-superset-common already sets - replicated here
# since this file replaces rather than extends the stock config.
DATABASE_DIALECT = os.environ.get("DATABASE_DIALECT", "postgresql")
DATABASE_HOST = os.environ.get("DATABASE_HOST", "postgres")
DATABASE_PORT = os.environ.get("DATABASE_PORT", "5432")
DATABASE_DB = os.environ.get("DATABASE_DB", "superset")
DATABASE_USER = os.environ.get("DATABASE_USER", "")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")

SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
)

FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
}

# A dedicated secret for signing/verifying guest tokens - see
# backend/app/superset_client.py, which mints these via Superset's own
# /api/v1/security/guest_token/ endpoint.
GUEST_TOKEN_JWT_SECRET = os.environ.get("SUPERSET_GUEST_TOKEN_JWT_SECRET", "change_me_guest_token_secret")
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # short-lived; the SDK refreshes automatically
GUEST_ROLE_NAME = "Public"

# The frontend origin needs both real CORS (for Superset's JS/API assets the
# embedded SDK loads) and a CSP exception to frame-ancestors (Superset's
# Talisman security headers block being framed by another origin by default -
# that default is exactly what embedding needs to relax, scoped to just this
# one trusted origin rather than disabled outright).
_FRONTEND_ORIGIN = os.environ.get("SUPERSET_ALLOWED_ORIGIN", "http://localhost:5173")

ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "origins": [_FRONTEND_ORIGIN],
}

TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "force_https": False,
    "content_security_policy": {
        "frame-ancestors": ["'self'", _FRONTEND_ORIGIN],
    },
}
