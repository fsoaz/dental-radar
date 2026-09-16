# Changelog

Human-readable history of Dental Radar. Commit messages are not a substitute for this file.

## Unreleased

### Added

- Versioned developer documentation: Diátaxis hub under `docs/`, getting-started tutorial, operator how-tos, API/CLI/environment/glossary reference, `CONTRIBUTING.md`, and this changelog. `docs/` is no longer gitignored.
- Enforced gitleaks, `pip-audit`, `npm audit`, Dependabot, immutable Action pins, and a reproducible backend `uv.lock`.
- Redis-backed rate limits shared across API replicas, with fail-closed behavior and readiness checks.
- Durable Postgres-backed rescore jobs with a dedicated worker and status polling in scoring settings.
- Accessible score/name table-header sorting and immediate scoring-band validation.
- `scripts/seed_demo_data.py`: 10 fictional clinics with locations, signals, scores, and canned enrichment text, so a local dashboard can be populated without paid providers.
- Documented host-mode development (API under uvicorn, dashboard under `npm run dev`) in `CONTRIBUTING.md`, including the Redis port compose does not publish.

### Changed

- Frontend toolchain moved to Next.js 16 (React 19) and Tailwind CSS v4. Conventions changed with the Next major — see `frontend/AGENTS.md`.
- CI frontend job runs `next build` in addition to lint and Vitest.
- Backend `ruff` pinned to 0.16.3; the pre-commit hook now pins the same version so local formatting matches the CI gate.
- Crawling and enrichment now follow the documented inward dependency direction: domain page evidence, application crawler errors/input fingerprints, and an injected resilient LLM adapter.
- The active `scoring_config` database row is the sole runtime scoring source; migration `0001` remains the immutable bootstrap definition.
- ORM metadata now declares the active-scoring-config uniqueness index and rescore-job status constraint already created by migrations `0001` and `0005`; this changes no database schema.

### Fixed

- Preserve endpoint-specific backend validation messages instead of rewriting scoring errors as clinic-filter guidance.
- Drive score-ranked pagination from the score index and add indexed clinic-name ordering.
- Persist `score --all` results per clinic while keeping durable worker rescoring atomic.
- Reject empty API scoring-band configuration in the dashboard instead of substituting hard-coded bands.
- An unsupported `AI_PROVIDER` returns 502 `ENRICHMENT_FAILED` from the enrich route instead of failing during request wiring.
- Run Alembic once through a migration service before API/worker startup rather than in every API replica.
- Documentation accuracy pass: `/health/ready` documented as returning 503 `degraded` (it checks Postgres **and** Redis, and never 500s on their failure), removed a `mypy`-in-CI claim that no workflow runs, corrected the `next lint` command, refreshed test counts, added the BFF proxy to the architecture diagram and folder trees, documented the frontend proxy's own error codes, and clarified the database-backed scoring source of truth.

### Removed

- Unused `scoring_defaults.yaml` and the direct PyYAML dependency (PyYAML remains a transitive dependency of `uvicorn[standard]`).
- Unused `SignalWeight` value object, `Address.formatted`, `infrastructure/db/session.get_db`, and crawler `meta` extraction.

### Security

- The frontend now proxies API requests through a same-origin server route and injects `API_KEY` server-side; browser `localStorage` no longer holds credentials.
- Removed unused `app_user` / JWT scaffolding through a reversible migration.
- Development and production operator surfaces bind to loopback by default; local secret files are created with mode `600`.
- Updated Next.js and affected transitive packages to clear the enforced High-severity dependency audit.
- Added CSP, anti-framing, MIME-sniffing, referrer, and browser permissions headers to the frontend.

## 2026-07-27 — QA remediation (pilot with reservations)

Fixes from the MVP QA review. Details: [qa_report §9](docs/internal/qa_report_2026-07-27.md#9-post-fix-verification-2026-07-27).

### Fixed

- Operator `X-API-Key` on mutating and billed routes; fail-closed when `API_KEY` is empty unless `ALLOW_UNAUTHENTICATED=true`.
- In-app per-IP rate limits; `X-Forwarded-For` trusted only via `RATE_LIMIT_TRUSTED_PROXIES`.
- Signal detection no longer wipes prior signals when a crawl fails.
- Scoring-config validation (contiguous bands, required weight keys).
- Discovery maps Places quota and auth failures to stable error codes.
- OpenAPI disabled when `APP_ENV=production`. Production compose binds the API to loopback by default.
- Scoring settings UI and clinic actions on the dashboard.

### Security

- Rate-limiter bypass via forged `X-Forwarded-For` closed (trust none unless proxies are allowlisted). Reverse proxy must overwrite `X-Forwarded-For`.

## 2026-06-19 — MVP (phases 1–7)

Initial vertical slice: discovery, signal detection, scoring, AI enrichment, dashboard, compose deploy/CI.
