"""
Superset config for embedded dashboards (Day 3, Step 5).

Mounted into the stock `apache/superset` image at
`/app/pythonpath/superset_config.py` (already on that image's PYTHONPATH, so
no custom Dockerfile is needed - see docker-compose.yml's superset service).

Everything here is additive to Superset's own defaults - it only turns on
what embedding needs:
  - EMBEDDED_SUPERSET feature flag
  - a guest-token JWT secret (separate from SUPERSET_SECRET_KEY - guest
    tokens are deliberately a different trust boundary)
  - CORS + a frame-ancestors CSP exception, both scoped to the frontend's
    origin specifically, not opened up broadly
"""
import os

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
