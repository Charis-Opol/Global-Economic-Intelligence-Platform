# Frontend

Vite + React 19 + TypeScript + Tailwind, with a small set of hand-written
shadcn/ui-style primitives (`src/components/ui/`) rather than a runtime
dependency on shadcn's own package - shadcn ships source to copy in, not a
library to import.

See the root [README.md](../README.md) and
[docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the full picture; this
file is just the local dev quickstart.

## Local development

```bash
npm install
cp .env.example .env.local   # point VITE_API_BASE_URL at a running backend
npm run dev
```

Requires the backend (`../backend`) running and reachable at
`VITE_API_BASE_URL` - the app itself has no offline/mock mode. See the root
README's "Running locally without Docker" section for the backend side of
this (including `../backend/.env.example` and
`../scripts/load_local_demo_data.py`, which loads real data into the
warehouse so the data pages aren't just empty tables).

## Scripts

- `npm run dev` - Vite dev server with hot reload
- `npm run build` - type-check (`tsc -b`) then production build to `dist/`
- `npm run preview` - serve the production build locally
- `npm run lint` - type-check only, no build

## Structure

```
src/
  pages/           one file per route (data/*.tsx are the six domain pages)
  components/
    ui/            hand-written shadcn-style primitives (button, card, table, ...)
    layout/        sidebar, topbar, theme toggle, app shell
    data/          generic paginated/filterable table (DataExplorer)
    dashboard/     stat cards
    superset/      embedded-dashboard component + the dashboard id map
  hooks/           use-auth (JWT session), use-theme (dark mode)
  lib/             api-client (typed fetch wrapper), jwt (decode-for-display), utils (cn)
  types/           TypeScript mirrors of backend/app/schemas.py
```

## Docker

`Dockerfile` has three stages: `dev` (what `docker-compose.yml` runs
locally, hot reload), `build` (compiles static assets), and `prod` (nginx
serving those assets, no Node.js at runtime). Build the production image
with:

```bash
docker build --target prod -t global-econ-intel-frontend:prod .
```

`VITE_*` env vars are inlined at build time - set them before `npm run
build` / `docker build`, not as a runtime env var on an already-built image.
