#!/bin/sh
set -eu

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
