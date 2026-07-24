#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-5}"

API_URL="${API_URL:-http://localhost:${API_PORT:-8000}/api/v1/health/ready}"

attempt=1
until curl -fsS "$API_URL" >/dev/null; do
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "Health check failed after ${MAX_ATTEMPTS} attempts: $API_URL" >&2
    exit 1
  fi
  echo "Waiting for API readiness (${attempt}/${MAX_ATTEMPTS})..."
  sleep "$SLEEP_SECONDS"
  attempt=$((attempt + 1))
done

echo "API is ready at $API_URL"
