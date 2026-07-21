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
