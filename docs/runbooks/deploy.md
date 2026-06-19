# Deployment Runbook

## Prerequisites

- Docker + Docker Compose on the target host
- Secrets stored outside the repo (`.env.production`, vault, or platform secret store)
- Registry access to `ghcr.io/<org>/dental-radar/{api,frontend}` if pulling CI-built images

## First-time setup

```bash
cp .env.production.example .env.production
# Edit secrets: POSTGRES_PASSWORD, JWT_SECRET, API keys, public URLs
mkdir -p backups
```

## Deploy latest `main`

```bash
export IMAGE_TAG=main
./scripts/deploy.sh
```

The deploy script:

1. Pulls API + frontend images (when configured)
2. Starts `docker-compose.prod.yml`
3. Runs Alembic migrations via the API entrypoint
4. Waits for `/api/v1/health/ready`

## Verify

```bash
curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready
open http://localhost:3000/clinics
```

## CI/CD

On push to `main`, GitHub Actions (`.github/workflows/deploy.yml`):

1. Runs backend + frontend tests
2. Builds and pushes images to GHCR (`:main` and `:sha-<commit>`)
3. Smoke-tests production compose + rollback script

## Backups

Schedule daily via cron on the host:

```bash
0 2 * * * /path/to/dental-radar/scripts/backup-postgres.sh
```

Backups land in `./backups/` as gzip SQL dumps.

## Monitoring

- **Liveness:** `GET /api/v1/health/live` — process up
- **Readiness:** `GET /api/v1/health/ready` — DB reachable post-migration
- **Logs:** JSON structured request logs when `LOG_JSON=true`

## Secrets

Never bake secrets into images. Provide via `.env.production` or orchestrator secret injection only.

**Note:** Changing `POSTGRES_PASSWORD` on an existing volume requires recreating the database volume (`docker compose ... down -v`) or altering the role password manually.
