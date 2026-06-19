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
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local` (default).

## Local development (backend)

```bash
cd backend
pip install -e ".[dev]"
export DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5432/dental_radar
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```bash
# Backend
cd backend
ruff check .
ruff format --check .
pytest

# Frontend
cd frontend
npm run lint
npm test
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
```

Requires `GOOGLE_PLACES_API_KEY` in `.env`.

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
