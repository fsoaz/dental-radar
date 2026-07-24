#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <previous-image-tag>" >&2
  echo "Example: $0 sha-abc1234" >&2
  exit 1
fi

PREVIOUS_TAG="$1"
export IMAGE_TAG="$PREVIOUS_TAG"

compose_args=(-f "$COMPOSE_FILE")
if [ -f "$ENV_FILE" ]; then
  compose_args=(--env-file "$ENV_FILE" "${compose_args[@]}")
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# GHCR/Docker require lowercase repository names; must match the lowercased
# path .github/workflows/deploy.yml pushes to.
if [ -n "${GITHUB_REPOSITORY:-}" ]; then
  export GITHUB_REPOSITORY="${GITHUB_REPOSITORY,,}"
fi

echo "Rolling back to tag=${IMAGE_TAG}..."
docker compose "${compose_args[@]}" pull api frontend || true
docker compose "${compose_args[@]}" up -d

"$ROOT_DIR/scripts/wait-for-health.sh"
echo "Rollback complete."
