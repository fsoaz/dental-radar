# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Dental Radar is a B2B sales-intelligence platform that ranks dental clinics by purchase
propensity. A Python/FastAPI backend runs a data pipeline (discover → detect → enrich →
score) over Postgres; a Next.js dashboard renders the ranked clinics.

## Commands

### Full stack (Docker)
```bash
cp .env.example .env
docker compose up --build          # Postgres (host :5433), API :8000, dashboard :3000
```
API docs at http://localhost:8000/docs.

### Backend
```bash
cd backend
pip install -e ".[dev]"
export DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar
alembic upgrade head                       # apply migrations
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ruff check . && ruff format --check . && pytest   # lint, format-check, test
pytest tests/unit/test_scoring_service.py         # single file
pytest -k "priority"                              # single test by name
```
Use host port `5433` against the Docker Postgres (`5433:5432`); `5432` for a native host Postgres.

### Frontend
```bash
cd frontend
cp .env.example .env.local          # set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm ci
npm run dev                         # :3000
npm run lint && npm test            # vitest; npm run build to production-build
npm test -- filter-bar              # single test file
```

### Pipeline CLI (run from `backend/`, needs `GOOGLE_PLACES_API_KEY` in `.env`)
```bash
python cli.py discover --query "dentist in Lisbon"   # ingest clinics from Google Places
python cli.py detect  --clinic-id <uuid> | --all     # crawl sites, detect buying signals
python cli.py enrich  --clinic-id <uuid> | --all [--force]   # LLM enrichment (force = re-run unchanged)
python cli.py score   --clinic-id <uuid> | --all     # recompute scores + priority
```

## Architecture

### Backend — Clean Architecture (`backend/app/`)
Four layers with a strict inward dependency rule. **`domain/` and `application/` must not
import `infrastructure/` or `presentation/`.** Wiring happens at the edges (`cli.py`,
`presentation/api/deps.py`), which construct concrete adapters and inject them into use cases.

- `domain/` — pure business logic: `entities/`, `value_objects/` (e.g. `Priority`,
  `ScoreBreakdown`, `SignalType`), `services/` (`ScoringService`, `SignalDetectionService`),
  and `repositories/` (abstract repo interfaces, not implementations).
- `application/` — orchestration: `use_cases/` (one per CLI/pipeline step:
  `discover_clinics`, `detect_signals`, `enrich_clinic`, `compute_score`), `ports/`
  (abstract interfaces for outside systems: `ClinicSource`, `WebsiteCrawler`, `LLMProvider`),
  and `dto/`.
- `infrastructure/` — concrete adapters: `repositories/` (SQLAlchemy impls of the domain
  repo interfaces), `db/` (`models.py` ORM + `mappers.py` translate ORM ↔ domain entities),
  `sources/google_places.py`, `crawler/`, `ai/`, `config/settings.py`, `migrations/` (Alembic).
- `presentation/` — FastAPI: `api/v1/` routers, `schemas/` (request/response Pydantic models,
  separate from domain), `deps.py` (DI), `middleware/`. `app/main.py` builds the app and maps
  domain exceptions (`ClinicNotFoundError`, `EnrichmentFailedError`) to JSON error envelopes
  (`{"error": {"code", "message", "details"}}`).

The repository pattern + mappers keep ORM models out of the domain. When adding a data field,
expect to touch the entity, the ORM model, the mapper, and a migration.

### Scoring & signals
Scores are derived: signals are detected per clinic, then `ScoringService` sums signal weights
via `ScoreBreakdown` and assigns a `PriorityLevel` from configurable thresholds. Default
weights/thresholds live in `infrastructure/config/scoring_defaults.yaml` and are surfaced
through the `ScoringConfig` entity (versioned — scores record the `config_version` used). The
`/scoring-config` endpoint exposes the active config to the dashboard.

### LLM enrichment
`infrastructure/ai/factory.py` selects a provider (`gpt` / `claude` / `gemini`) from
`AI_PROVIDER`, with retries (exponential backoff on `TransientLLMError`) and an optional
`AI_FALLBACK_PROVIDER`. Enrichment is idempotent: an input fingerprint skips unchanged clinics
unless `--force`. Prompts are versioned text files under `ai/prompts/`.

### Frontend (`frontend/`)
Next.js 15 App Router + React 19, Tailwind, shadcn/ui (`components/ui/`). All backend access
goes through `lib/api.ts` (typed against `lib/types.ts`); do not call `fetch` elsewhere. Note
the dual base-URL resolution in `getApiBaseUrl()` — server components use `API_URL`, the
browser uses `NEXT_PUBLIC_API_URL`. List filters round-trip through URL search params
(`buildClinicListQuery` / `clinicListQueryToSearchParams`), so the clinics table is
deep-linkable and server-rendered from the query string.

## Conventions

- **Python**: 3.12, 4-space indent, type hints, Ruff (double quotes, 100-col, `E/F/I/UP`).
  `snake_case` / `PascalCase` / `UPPER_SNAKE_CASE`.
- **TypeScript**: strict, ESLint. `PascalCase` components, `camelCase` values,
  `kebab-case.tsx` filenames.
- **Tests**: pytest under `backend/tests/{unit,integration,api}` (`test_*.py`); Vitest +
  React Testing Library under `frontend/tests/` (`*.test.tsx`). **Mock Google Places,
  crawlers, and LLM providers — CI must never hit live external services.** Targets: ~90%
  coverage on domain services, ~70% overall backend.
- **Commits**: Conventional Commits, imperative subject ≤50 chars; branches `feat/...`,
  `fix/...`. Lint + test + build must pass before merging to `main`.
- **Secrets**: copy the committed `.env.example` files; never commit `.env`, `.env.local`,
  or production secrets.

### Frontend dependency safety
Next.js 15 + React 19 have tight peer constraints. Do **not** run `npm audit fix --force` or
use `--legacy-peer-deps` — a forced fix can downgrade `next` from 15.x to 9.x. Resolve
advisories with targeted, compatible upgrades. If `next` unexpectedly changes major versions,
restore the lockfile and reinstall:
```bash
git restore package.json package-lock.json && npm ci
```

## Deployment

Push to `main` runs CI, builds/pushes GHCR images, and smoke-tests the prod compose stack
(`.github/workflows/deploy.yml`). Prod stack is `docker-compose.prod.yml`; deploy/rollback via
`scripts/deploy.sh` and `scripts/rollback.sh`. Health probes: `/api/v1/health/live`
(liveness), `/api/v1/health/ready` (readiness post-migration), `/api/v1/health` (legacy alias).
See `docs/runbooks/`.
