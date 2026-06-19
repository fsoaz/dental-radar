# Dental Radar — Documentation

B2B sales-intelligence platform for ranking dental clinics by purchase propensity.

**MVP status:** Phases 1–7 complete (2026-06-19). Ready for pilot.

---

## Start here

| Doc | Purpose |
|-----|---------|
| [context/product.md](context/product.md) | PRD, user stories, acceptance criteria |
| [context/architecture.md](context/architecture.md) | System design, domain model, DB schema, API, folder layout |
| [context/roadmap.md](context/roadmap.md) | Phase plan, sprint breakdown, dependencies |

## Run the platform

```bash
# Local dev stack
cp .env.example .env
docker compose up --build

# Dashboard: http://localhost:3000/clinics
# API:       http://localhost:8000/api/v1/health/ready
# API docs:  http://localhost:8000/docs
```

See the root [README.md](../README.md) for backend/frontend dev setup, CLI commands, and production deployment.

## Pilot workflow (end-to-end)

Run after the stack is up and `GOOGLE_PLACES_API_KEY` / LLM keys are set:

```bash
cd backend
python cli.py discover --query "dentist in Lisbon"
python cli.py detect --all
python cli.py score --all
python cli.py enrich --all

# Open dashboard → filter Hot/Immediate → open clinic detail
```

## Phase tasks (implementation checklist)

| Phase | Doc | Status |
|-------|-----|--------|
| 1 Foundation | [tasks/phase-1-foundation.md](tasks/phase-1-foundation.md) | Done |
| 2 Discovery | [tasks/phase-2-discovery.md](tasks/phase-2-discovery.md) | Done |
| 3 Signals | [tasks/phase-3-signals.md](tasks/phase-3-signals.md) | Done |
| 4 Scoring | [tasks/phase-4-scoring.md](tasks/phase-4-scoring.md) | Done |
| 5 AI Enrichment | [tasks/phase-5-ai-enrichment.md](tasks/phase-5-ai-enrichment.md) | Done |
| 6 Dashboard | [tasks/phase-6-dashboard.md](tasks/phase-6-dashboard.md) | Done |
| 7 Deployment | [tasks/phase-7-deployment.md](tasks/phase-7-deployment.md) | Done |

## Standards

| Doc | Purpose |
|-----|---------|
| [standards/conventions.md](standards/conventions.md) | Coding style, git, env vars |
| [standards/api_rules.md](standards/api_rules.md) | REST conventions, errors, pagination |
| [standards/ai_agent_rules.md](standards/ai_agent_rules.md) | LLM provider usage, prompts, retries |
| [standards/testing.md](standards/testing.md) | Test strategy, CI expectations |

## Operations

| Doc | Purpose |
|-----|---------|
| [runbooks/deploy.md](runbooks/deploy.md) | Production deploy, health probes, backups |
| [runbooks/rollback.md](runbooks/rollback.md) | Roll back images, migration downgrade, restore |

**Scripts:** `scripts/deploy.sh`, `scripts/rollback.sh`, `scripts/backup-postgres.sh`, `scripts/wait-for-health.sh`

**Compose files:**
- `docker-compose.yml` — local development
- `docker-compose.prod.yml` — production

**CI/CD:**
- `.github/workflows/ci.yml` — lint + test on PR/push
- `.github/workflows/deploy.yml` — build/push GHCR images + smoke deploy on `main`

## Execution tracking

| Doc | Purpose |
|-----|---------|
| [execution/current_task.md](execution/current_task.md) | Current focus / handoff |
| [execution/work_log.md](execution/work_log.md) | Session log (append-only) |
| [execution/test_evidence.md](execution/test_evidence.md) | Per-sprint test proof |
| [execution/review_notes.md](execution/review_notes.md) | PR review findings |

## Test counts (MVP)

| Suite | Count |
|-------|-------|
| Backend (`pytest`) | 56 |
| Frontend (`vitest`) | 6 |

Postgres test DB host port: **5433** (compose maps `5433:5432` to avoid local conflicts).

## Not yet implemented (post-MVP)

- JWT auth (`POST /auth/login`) — API is open in MVP
- Playwright E2E tests
- Message broker / async job queue (batch jobs use CLI + cron)
