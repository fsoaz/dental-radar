# Changelog

Human-readable history of Dental Radar. Commit messages are not a substitute for this file.

## Unreleased

### Added

- Versioned developer documentation: Diátaxis hub under `docs/`, getting-started tutorial, operator how-tos, API/CLI/environment/glossary reference, `CONTRIBUTING.md`, and this changelog. `docs/` is no longer gitignored.
- Enforced gitleaks, `pip-audit`, `npm audit`, Dependabot, immutable Action pins, and a reproducible backend `uv.lock`.
- Redis-backed rate limits shared across API replicas, with fail-closed behavior and readiness checks.
- Durable Postgres-backed rescore jobs with a dedicated worker and status polling in scoring settings.
- Accessible score/name table-header sorting and immediate scoring-band validation.

### Fixed

- Preserve endpoint-specific backend validation messages instead of rewriting scoring errors as clinic-filter guidance.
- Drive score-ranked pagination from the score index and add indexed clinic-name ordering.
- Run Alembic once through a migration service before API/worker startup rather than in every API replica.

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
