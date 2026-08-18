# Deploy to production

Related: [environment](../reference/environment.md) · [rollback](rollback.md) · [troubleshoot](troubleshoot.md)

## Prerequisites

- Docker + Docker Compose on the target host
- Secrets stored outside the repo (`.env.production`, vault, or platform secret store)
- Registry access to `ghcr.io/<org>/dental-radar/{api,frontend}` if pulling CI-built images

## Pre-flight (security)

Confirm these before promoting a pilot or production deploy:

| Check | Expected |
|---|---|
| `API_KEY` | Non-empty; backend and frontend BFF receive the same server-only value |
| `ALLOW_UNAUTHENTICATED` | `false` / unset (mutating routes fail closed without a key) |
| `APP_ENV` | `production` (disables `/docs` and `/openapi.json`) |
| `API_URL` | Frontend server target, normally `http://api:8000/api/v1` in Compose |
| `REDIS_URL` | Reachable Redis used for shared rate-limit state |
| `API_BIND` | `127.0.0.1` unless an edge proxy elsewhere terminates TLS |
| `FRONTEND_BIND` | `127.0.0.1`; expose only through the trusted operator proxy/network |
| `FORWARDED_ALLOW_IPS` | Empty (trust nobody) **or** only your reverse-proxy address |
| `RATE_LIMIT_TRUSTED_PROXIES` | Same trust set as `FORWARDED_ALLOW_IPS` |
| Reverse proxy `X-Forwarded-For` | **Overwrite** with `$remote_addr` (do not append client-supplied values) |

A misconfigured forwarded-header trust list silently re-opens per-IP rate-limit bypass. Defaults (empty) are safe.

The local stack binds Postgres, Redis, API, and frontend to `127.0.0.1`. Do not loosen those bindings when paid-provider keys are configured.

## First-time setup

```bash
install -m 600 .env.production.example .env.production
# Edit secrets: POSTGRES_PASSWORD and provider/API keys
mkdir -p backups
```

## Deploy latest `main`

```bash
export IMAGE_TAG=main
./scripts/deploy.sh
```

The deploy script:

1. Pulls the tagged API + frontend images from GHCR (fails hard if the pull fails —
   it no longer falls back to rebuilding from the local checkout)
2. Starts `docker-compose.prod.yml` from those pulled images
3. Runs Alembic migrations via the API entrypoint
4. Waits for `/api/v1/health/ready` (Postgres and Redis)

## Verify

```bash
curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready
open http://localhost:3000/clinics
```

## CI/CD

On push to `main`, GitHub Actions (`.github/workflows/deploy.yml`):

1. Runs gitleaks, locked dependency installs, backend/frontend lint and tests, plus high/critical dependency audit gates
2. Builds and pushes images to GHCR (`:main` and `:sha-<commit>`)
3. Smoke-tests production compose + rollback script on an ephemeral CI runner, then tears it down

**This workflow does not deploy to any real host.** "Deploy latest `main`" above (running
`scripts/deploy.sh` against your production host) is a separate, manual step — CI only
verifies the compose stack boots and publishes images for that script to pull.

## Backups

Schedule daily via cron on the host:

```bash
0 2 * * * /path/to/dental-radar/scripts/backup-postgres.sh
```

Backups land in `./backups/` as gzip SQL dumps.

## Monitoring

- **Liveness:** `GET /api/v1/health/live` — process up
- **Readiness:** `GET /api/v1/health/ready` — Postgres and Redis reachable
- **Logs:** JSON structured request logs when `LOG_JSON=true`

## Secrets

Never bake secrets into images. Provide via `.env.production` or orchestrator secret injection only.

**Note:** Changing `POSTGRES_PASSWORD` on an existing volume requires recreating the database volume (`docker compose ... down -v`) or altering the role password manually.
