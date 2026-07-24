#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
IMAGE_TAG="${IMAGE_TAG:-main}"

compose_args=(-f "$COMPOSE_FILE")
if [ -f "$ENV_FILE" ]; then
  compose_args=(--env-file "$ENV_FILE" "${compose_args[@]}")
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

export IMAGE_TAG

# GHCR/Docker require lowercase repository names; .github/workflows/deploy.yml
# pushes images to a lowercased path, so pulling must match or it 404s/rejects
# for any GITHUB_REPOSITORY containing uppercase characters.
if [ -n "${GITHUB_REPOSITORY:-}" ]; then
  export GITHUB_REPOSITORY="${GITHUB_REPOSITORY,,}"
fi

echo "Deploying Dental Radar (tag=${IMAGE_TAG})..."
docker compose "${compose_args[@]}" pull api frontend
docker compose "${compose_args[@]}" up -d

"$ROOT_DIR/scripts/wait-for-health.sh"
echo "Deploy complete."
