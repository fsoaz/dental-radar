# Dental Radar

B2B sales-intelligence platform that ranks dental clinics by purchase propensity.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- API health: http://localhost:8000/api/v1/health
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000/clinics
- Postgres (host): `localhost:5433` when using Docker Compose

## Local development (frontend)

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local` (default).

### Frontend dependency audits

This project uses Next.js 15 with React 19. Inspect an audit report before changing
dependencies:

```bash
cd frontend
npm audit
```

Do not run `npm audit fix --force` or bypass peer-dependency checks with
`--legacy-peer-deps`. A forced audit fix can select an incompatible Next.js major
version. Resolve advisories with targeted, compatible dependency upgrades, then run
the frontend lint, test, and build commands.

If an audit command unexpectedly changes `next` from 15.x to 9.x, restore the
tracked dependency files and reinstall from the lockfile:

```bash
cd frontend
git diff -- package.json package-lock.json
git restore package.json package-lock.json
npm ci
npm audit
npm run lint
npm test
npm run build
```

## Local development (backend)

```bash
cd backend
pip install -e ".[dev]"
export DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Port `5433` targets the Postgres exposed by `docker compose up` (mapped `5433:5432`).
If you run your own Postgres directly on the host instead, use `5432`.

## Tests

```bash
# Backend
cd backend
ruff check .
ruff format --check .
DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test pytest

# Frontend
cd frontend
npm run lint
npm test
```

Backend integration/API tests need a Postgres test database. With Docker Compose, start
Postgres and create the test DB once:

```bash
docker compose up -d postgres
docker compose exec postgres createdb -U dental_radar dental_radar_test
```

### Pre-commit hooks

Ruff lint/format run in CI (`ruff check .`, `ruff format --check .`). Install the
pre-commit hook once to catch violations before pushing:

```bash
pip install pre-commit
pre-commit install
```

## CLI

```bash
cd backend
python cli.py discover --query "dentist in Lisbon"
python cli.py detect --clinic-id <uuid>
python cli.py detect --all
python cli.py score --clinic-id <uuid>
python cli.py score --all
python cli.py enrich --clinic-id <uuid>
python cli.py enrich --all
python cli.py enrich --clinic-id <uuid> --force
python cli.py test-connection
```

Requires `GOOGLE_PLACES_API_KEY` for discovery and an LLM API key for enrichment /
`test-connection`.

## Production deployment

See [`docs/runbooks/deploy.md`](docs/runbooks/deploy.md) and [`docs/runbooks/rollback.md`](docs/runbooks/rollback.md).

```bash
cp .env.production.example .env.production
# Edit secrets (POSTGRES_PASSWORD, JWT_SECRET, public URLs)

./scripts/deploy.sh              # deploy IMAGE_TAG=main
./scripts/rollback.sh sha-<tag>  # roll back to previous image
./scripts/backup-postgres.sh     # manual backup (schedule via cron)
```

**Health probes**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health/live` | Liveness — process up |
| `GET /api/v1/health/ready` | Readiness — DB OK post-migration |
| `GET /api/v1/health` | Legacy alias for readiness |

**CI/CD:** Push to `main` runs tests, builds/pushes GHCR images, and smoke-tests production compose + rollback (`.github/workflows/deploy.yml`).

**Local dev stack:** `docker compose up --build`  
**Production stack:** `docker compose -f docker-compose.prod.yml up -d`

## Documentation

See [`docs/`](docs/) for the full documentation index — product requirements, architecture, phase tasks, runbooks, and standards.

Quick links:
- [docs/README.md](docs/README.md) — documentation index + pilot workflow
- [docs/runbooks/deploy.md](docs/runbooks/deploy.md) — production deployment
- [docs/runbooks/rollback.md](docs/runbooks/rollback.md) — rollback procedures
