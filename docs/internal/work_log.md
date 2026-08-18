# Work Log

- 2026-08-18: Closed the current QA report findings — endpoint-specific scoring errors and inline band validation, durable Postgres rescore jobs with a serialized worker and polling UI, index-driven score/name pagination, one-shot Compose migrations, accessible table-header sorting, frontend security headers, and synchronized operator/reference/internal docs. Verification: 90 backend tests, 22 frontend tests, lint/build clean, reversible migration, live headers, and browser render check.
- 2026-08-17: Implemented and documented security audit remediation — CI secret/dependency gates and Dependabot, locked backend dependencies with uv, Redis-shared fail-closed rate limiting, same-origin frontend BFF with server-only API key, removal migration for dormant auth scaffolding, loopback-only service bindings, and mode-600 env-file guidance. Updated the operator, contributor, architecture, API, environment, troubleshooting, and test-evidence docs to match.

> Append-only. Newest first. One entry per work session. Format below.

## Template
```
### YYYY-MM-DD — <name>
- Phase/Sprint: <e.g. S1 / Phase 1>
- Done: <what shipped>
- Decisions: <any choices made + why>
- Next: <handoff>
```

---

### 2026-08-17 — Developer docs architecture
- Phase/Sprint: docs / post-QA
- Done: Stopped gitignoring `docs/`. Restructured to Diátaxis (tutorials, how-to, explanation, reference, standards, internal). Added getting-started, pilot pipeline, tune-scoring, troubleshoot, API/CLI/env/glossary, `ai_agent_rules.md`, `CONTRIBUTING.md`, `CHANGELOG.md`. Slimmed root README.
- Decisions: Audience = engineers + operators. Execution notes stay in-repo under `docs/internal/`, labeled not for operators. FastAPI `/docs` remains schema SSOT (no checked-in OpenAPI).
- Next: Pilot with real data; measure Hot-clinic contact quality.

### 2026-07-27 — MVP QA review + remediation
- Phase/Sprint: QA / post-S7
- Done: Full MVP QA ([qa_report_2026-07-27.md](qa_report_2026-07-27.md)); fixed P0-1/P0-2 and P1-3…P1-10 (signal wipe, scoring-config validation, operator `X-API-Key`, rate limits, discovery errors, prod URL/bind, scoring settings UI + clinic actions, related P2/P3). Post-fix verification closed both P0s and all P1s; remediated rate-limiter XFF bypass (§9.3); fail-closed auth (`ALLOW_UNAUTHENTICATED`); frontend tests 6→15; backend tests →87. Docs synced (api_rules, architecture, deploy pre-flight, README).
- Decisions: Pilot call = **Yes, with reservations** (network isolation + deploy pre-flight). JWT login still post-MVP; operator API key covers mutating routes. Trust nobody for forwarded headers by default.
- Next: Pilot with real data; measure Hot-clinic contact quality.

### 2026-07-03 — LLM provider/config hardening
- Phase/Sprint: Hardening / post-S7
- Done: Restored non-2xx LLM HTTP failures, moved OpenAI base URL validation into settings, narrowed Python CORS defaults, replaced the standalone LLM script with `dental-radar test-connection`, and added focused tests. Backend suite now reports 66 passing tests.
- Decisions: Keep broad localhost CORS origins only in dev-scoped env/compose templates; keep provider constructors infallible so fallback providers are not masked by config validation.
- Next: Pilot with real data; run `python cli.py test-connection` before batch enrichment.

### 2026-06-19 — Security review fixes
- Phase/Sprint: Hardening / post-S7
- Done: Applied 3 fixes from security review — SSRF guard in `HttpxWebsiteCrawler` (scheme + private/metadata IP denylist, manual per-hop redirect validation), Gemini API key moved from query string to `x-goog-api-key` header, Google Places discovery capped via new `PLACES_MAX_PAGES` setting (default 3). Added `tests/unit/test_website_crawler.py` (5 tests); updated `.env(.production).example`, architecture §8, api_rules, review_notes.
- Decisions: JWT auth on mutating routes (`PUT /scoring-config` etc.) deferred to Phase 2+; documented network-isolation + edge rate-limit as interim compensating control.
- Next at the time: pilot with real data; the auth and rate-limit work was completed by the 2026-08-17 security hardening pass.

### 2026-06-19 — Documentation refresh (MVP complete)
- Phase/Sprint: Docs / post-S7
- Done: Added `docs/README.md` index; updated roadmap (all phases ✅), architecture (API status, deployment §8, folder tree), standards (api/conventions/testing), execution docs (pilot checklist, test summary, review notes), product.md status, root README doc links.
- Decisions: Document auth as post-MVP; keep legacy `/health` documented as readiness alias.
- Next: Pilot with real data.

### 2026-06-19 — Phase 7 Deployment
- Phase/Sprint: S7 / Phase 7
- Done: Multi-stage API Dockerfile + entrypoint migrations, production `docker-compose.prod.yml`, GHCR deploy workflow (test → build → push → smoke + rollback), live/ready health probes, JSON request logging, backup/rollback/deploy scripts, runbooks.
- Decisions: Migrations gate readiness via entrypoint; secrets only via env files; rollback = redeploy previous image tag (Alembic downgrade documented separately).
- Next: Pilot with real data.

### 2026-06-19 — Phase 6 Dashboard
- Phase/Sprint: S6 / Phase 6
- Done: Next.js 15 app (App Router, TypeScript, Tailwind, shadcn-style UI), typed API client, ranked clinic list with search/filters/pagination, clinic detail with signals/score/AI breakdown, CORS on API, Docker + CI frontend job, 6 Vitest component tests.
- Decisions at the time: client-side fetch via `NEXT_PUBLIC_API_URL`; superseded on 2026-08-17 by the same-origin server-side BFF using `API_URL` and `API_KEY`. Priority-colored badges remain aligned to scoring bands.
- Next: Phase 7 — deployment hardening.

### 2026-06-19 — Phase 5 AI Enrichment
- Phase/Sprint: S5 / Phase 5
- Done: `LLMProvider` port, `ClinicAIInput`/`EnrichmentResult` DTOs, versioned prompt, GPT/Claude/Gemini providers via httpx, factory with retries + optional fallback, enrichment repo + `input_fingerprint` cache, `EnrichClinic`/`EnrichAllClinics`, `POST /clinics/{id}/enrich`, CLI `enrich --all/--clinic-id [--force]`, 16 new tests (49 total passing).
- Decisions: Skip re-enrich when input fingerprint unchanged unless `force`; one schema repair retry before failing; providers share base class with identical output schema.
- Next: Phase 6 — dashboard.

### 2026-06-19 — Phase 4 Scoring Engine
- Phase/Sprint: S4 / Phase 4
- Done: `ScoringService`, `ScoreBreakdown`, `PriorityLevel`, score repo, `ComputeScore`/`RescoreAll`, scoring-config GET/PUT with optional rescore, `POST /clinics/{id}/score`, extended list filters + default `sort=-score`, CLI `score --all/--clinic-id`, 12 new tests (33 total passing).
- Decisions: Scores recompute from active config weights (not stale signal weights); list sorting uses scalar subqueries to avoid Postgres DISTINCT/ORDER BY issues.
- Next: Phase 5 — AI enrichment.

### 2026-06-19 — Phase 3 Signal Detection
- Phase/Sprint: S3 / Phase 3
- Done: `HttpxWebsiteCrawler`, `SignalDetectionService` (5 detectors), `DetectSignals`/`ListClinicSignals` use cases, signal repo with full replace on re-run, API (`POST /signals:detect`, `GET /signals`), CLI `detect --clinic-id/--all`, 11 new tests (21 total passing).
- Decisions: Full signal replace on each detect run (removes stale types); weights loaded from active `scoring_config`; crawl failures return 0 signals with skip_reason.
- Next: Phase 4 — scoring engine.

### 2026-06-19 — Phase 2 Clinic Discovery
- Phase/Sprint: S2 / Phase 2
- Done: `ClinicSource` port + `GooglePlacesClient`, domain entities (`Clinic`, `Location`, `Address`), `SqlAlchemyClinicRepository` upsert by `place_id`, `DiscoverClinics`/`ListClinics`/`GetClinic` use cases, API endpoints (`POST /clinics/discover`, `GET /clinics`, `GET /clinics/{id}`), CLI `discover --query`, 7 new tests (10 total passing).
- Decisions: Google Places API (New) text search with pagination; upsert updates rating/reviews on re-run; list/detail return nullable score/enrichment until later phases.
- Next: Phase 3 — signal detection.

### 2026-06-19 — Phase 1 Foundation
- Phase/Sprint: S1 / Phase 1
- Done: Scaffolded monorepo — FastAPI backend (Clean Architecture layers), SQLAlchemy models for all 7 tables, Alembic initial migration with `scoring_config` v1 seed, `GET /api/v1/health`, docker-compose (api + postgres + frontend placeholder), GitHub Actions CI (ruff + pytest), smoke/integration tests.
- Decisions: Sync SQLAlchemy for MVP; Postgres host port 5433 in compose to avoid local conflicts; health endpoint verifies DB with `SELECT 1`.
- Next: Phase 2 — Google Places discovery.

### 2026-06-19 — fsoaz
- Phase/Sprint: Docs
- Done: Populated `docs/` with all 10 deliverables — PRD + user stories (product.md), architecture/domain/DB/API/folders (architecture.md), roadmap + sprints (roadmap.md), standards (conventions, api_rules, ai_agent_rules, testing), per-phase technical tasks (tasks/phase-1..7), execution templates.
- Decisions: Default LLM provider = OpenAI GPT (Claude/Gemini pluggable via `AI_PROVIDER`). Scoring weights/bands stored in `scoring_config` table (configurable, no redeploy). Discovery MVP source = Google Places behind `ClinicSource` port.
- Next: Phase 1 — backend skeleton + DB + CI.
