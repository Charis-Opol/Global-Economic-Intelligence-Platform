# Deployment guide

This is a **guide**, not a deployment - Day 3, Step 10 asked for documentation
of how to deploy; actually standing this up on a cloud account is Day 4, and
needs real provider credentials this environment doesn't have. Everything
below is what to do once you're ready for that.

## What has to go where

The stack is nine services (`docker-compose.yml`), which map to three
different deployment shapes:

| Service(s)                                                        | Shape                          | Notes |
|---------------------------------------------------------------------|---------------------------------|-------|
| `backend`, `frontend`                                                | Stateless web services           | Scale horizontally at will. `frontend`'s `prod` Docker stage (nginx serving the static build) is what you deploy - not the `dev` stage docker-compose uses locally. |
| `airflow-webserver`, `airflow-scheduler`, `airflow-worker`, `mlflow`, `superset` | Stateful-ish long-running services | Each needs its metadata store (Postgres) and, for Airflow, Redis (Celery broker) reachable. Don't scale `airflow-scheduler` beyond 1 without enabling Airflow's HA scheduler support. |
| `postgres`, `redis`, `minio`                                         | Data stores                     | Prefer managed equivalents where available (RDS/Cloud SQL for Postgres, ElastiCache/Memorystore for Redis, S3/GCS for object storage instead of self-hosted MinIO) - the app already talks to MinIO over the S3 API, so swapping the endpoint is a config change, not a code change. |

`warehouse.duckdb` is a single file, not a network service - whatever runs
`backend`, `spark`, and the Airflow workers all need it on a **shared,
persistent volume** (or you switch it to a network filesystem / object
storage-backed path). This is the one piece of local-disk state that doesn't
map cleanly onto typical "stateless container" platforms (Render, Railway,
Cloud Run) - see the per-target notes below.

## Environment variables

Everything in `.env.example` needs a real value. Highlights that are easy to
miss:

- `JWT_SECRET_KEY`, `SUPERSET_GUEST_TOKEN_JWT_SECRET`, `AIRFLOW_FERNET_KEY`,
  `SUPERSET_SECRET_KEY` - all must be real random secrets in production, not
  the `change_me` placeholders.
- `FRONTEND_ORIGIN` - must be the frontend's real deployed URL (not
  `localhost:5173`), or CORS and Superset embedding both break silently.
- Every `*_BASE_URL` / `*_ENDPOINT` (`AIRFLOW_BASE_URL`, `MLFLOW_TRACKING_URI`,
  `SUPERSET_BASE_URL`, `MINIO_ENDPOINT`) needs to point at wherever that
  service actually lives once it's not all on one Docker network reachable
  by service name.
- `VITE_API_BASE_URL` / `VITE_SUPERSET_DOMAIN` are baked into the frontend
  **at build time** (Vite inlines `import.meta.env.*` during `npm run
  build`) - set them before building the image, not as a runtime env var on
  an already-built container.

## Per-target notes

These are genuinely different shapes of platform - pick one, don't mix:

**Render / Railway / DigitalOcean App Platform** (simplest to start with):
container-per-service, managed Postgres/Redis add-ons, but no first-class
shared-volume primitive across services on most of these - you'll likely
need to move `warehouse.duckdb` onto an attached persistent disk (where
supported) or reconsider the warehouse as a network-accessible file (e.g.
mount via a shared NFS-backed volume, or move to a client/server database
if the file-based model becomes a real constraint at this stage).

**AWS / GCP / Azure** (more control, more setup): ECS/Fargate or GKE/AKS for
the containers, RDS/Cloud SQL for Postgres, ElastiCache/Memorystore for
Redis, S3/GCS/Blob Storage in place of MinIO, and EFS/Filestore/Azure Files
for the shared DuckDB file if you keep the single-file warehouse model.
Airflow and Superset both have official Helm charts if you're on Kubernetes -
prefer those over hand-rolling the Docker Compose topology in raw manifests.

## Before going live, in order

1. Regenerate every secret in `.env` for real (see `.env.example`'s inline
   generation commands) - never reuse local-dev values.
2. Build the frontend's `prod` target (`docker build --target prod
   ./frontend`), not `dev` - confirm `docker run` serves it and routes
   correctly (client-side routes need the nginx `try_files` fallback in
   `frontend/nginx.conf`).
3. Run the full Day 1 pipeline once against real API keys (`NEWSAPI_KEY` at
   minimum) so the warehouse actually has data before anyone hits the API.
4. Import `superset/dashboards/` into the live Superset instance and
   **verify each chart renders** - see that folder's README for exactly what
   to check; it was authored without a live Superset to validate against.
5. Confirm the four nightly training DAGs (`train_*_forecast`) have run at
   least once and each model has a `champion` alias, or `/predictions` will
   404 for every domain.
6. Point DNS/domains at the deployed frontend and backend, update
   `FRONTEND_ORIGIN` and `VITE_API_BASE_URL` to match, and rebuild the
   frontend image (step 2) with the new build-time env vars.
