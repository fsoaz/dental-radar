FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY app ./app
COPY cli.py ./cli.py
RUN uv sync --locked --no-dev --no-editable --no-cache

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 app && adduser --system --uid 1001 --gid 1001 app

COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini ./
COPY app ./app
COPY cli.py ./cli.py
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R app:app /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/app/.venv/bin:$PATH
ENV PORT=8000

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/v1/health/live || exit 1

ENTRYPOINT ["/entrypoint.sh"]
