# Current Task

> Single source of truth for what's being worked on right now. Update at the start of each work session.

- **Phase:** MVP complete (Phases 1–7) + security hardening (2026-08-17)
- **Sprint:** S7 done; audit remediation done
- **Status:** Pilot-ready behind the documented operator/network boundary; the [2026-07-27 QA call](qa_report_2026-07-27.md#96-revised-release-recommendation) is historical context
- **Owner:** —
- **Docs index:** [README.md](../README.md) (hub) · this folder is [internal](README.md)

## Now
_QA P0/P1 defects and the 2026-08-17 security hardening are closed and verified. Focus: pilot with real clinic data behind network isolation; measure scoring quality._

## Pilot checklist

1. Configure `.env` / `.env.production` — `API_KEY`, `GOOGLE_PLACES_API_KEY`, LLM keys; prod: `ALLOW_UNAUTHENTICATED=false`
2. Complete [deploy pre-flight](../how-to/deploy.md#pre-flight-security) (`FORWARDED_ALLOW_IPS` / `RATE_LIMIT_TRUSTED_PROXIES`, `API_URL`, Redis, bind)
3. `docker compose up --build` (local) or `./scripts/deploy.sh` (prod)
4. From `backend/`: `uv sync --locked --extra dev`, then `uv run dental-radar discover --query "dentist in <region>"`
5. `uv run dental-radar test-connection`
6. `uv run dental-radar detect --all && uv run dental-radar score --all && uv run dental-radar enrich --all`
7. Open http://localhost:3000/clinics — filter Hot/Immediate, review detail pages
8. Tune weights via http://localhost:3000/settings/scoring (the server-side BFF supplies the key) or `PUT /api/v1/scoring-config` with `X-API-Key`

## Blockers
- None for a network-isolated pilot. OpenRouter/LLM credits required for live enrich.

## Post-MVP / open from QA §9.5
- Async rescore / job queue (P1-8)
- Index-driven list sort (P2-15)
- Multi-page / locale crawl depth (P2-19)
- Migration init job before multi-replica (P3-23)
- Crawl status fields; social URLs / services
- Per-user authentication
- Playwright E2E
- Measured Hot-clinic contact quality metric
