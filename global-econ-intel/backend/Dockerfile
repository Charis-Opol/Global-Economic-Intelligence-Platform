# Built automatically by `docker compose up --build` (docker-compose.yml's
# backend service has no `target:`, so Docker just builds this file's last
# stage - there's only one runtime outcome here, unlike frontend/Dockerfile's
# dev/build/prod split).
#
# To run this backend without Docker at all (e.g. Docker Desktop isn't
# running, or you just want faster iteration), see the root README's
# "Running locally without Docker" section instead - that's a plain
# `uvicorn app.main:app --reload` process, not this image.

# ---- builder: resolve/compile dependencies once, discard the toolchain ----
FROM python:3.13-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- final: slim runtime image, no compilers, non-root user ----
FROM python:3.13-slim

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY app ./app

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000
# --reload is a local-dev convenience (this image is what docker-compose runs
# for local development) - a real deployment (Day 4) drops it and adds a
# worker count / process manager instead.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
