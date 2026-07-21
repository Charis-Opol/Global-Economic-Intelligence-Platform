# Three stages, three different ways this gets built - pick the one that
# matches what you're doing:
#
#   docker compose up --build        -> builds `dev` (docker-compose.yml
#                                        pins `target: dev` on the frontend
#                                        service) - hot reload, same as
#                                        `npm run dev` but containerized.
#   docker build --target prod .     -> the real deployable image: static
#                                        assets built once, served by nginx,
#                                        no Node.js in the final image at all.
#   (no Docker at all)               -> see the root README's "Running
#                                        locally without Docker" section -
#                                        just `npm install && npm run dev`,
#                                        no image involved.
#
# `build` (compiling static assets) is an intermediate stage `prod` depends
# on - it's never targeted directly.

# ---- deps: installed once, cached across the dev and build stages ----
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- dev: what docker-compose runs locally (hot reload) ----
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- build: compile static assets ----
FROM deps AS build
COPY . .
RUN npm run build

# ---- prod: static assets behind nginx, no Node/npm at runtime ----
FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
