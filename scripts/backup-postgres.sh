#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FILE="$BACKUP_DIR/dental_radar_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

compose_args=(-f "$COMPOSE_FILE")
if [ -f "$ENV_FILE" ]; then
  compose_args=(--env-file "$ENV_FILE" "${compose_args[@]}")
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-dental_radar}"
POSTGRES_DB="${POSTGRES_DB:-dental_radar}"

echo "Creating backup: $OUTPUT_FILE"
docker compose "${compose_args[@]}" exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUTPUT_FILE"

echo "Backup complete ($(du -h "$OUTPUT_FILE" | awk '{print $1}'))"
