# Test Evidence

> Per-sprint proof that acceptance criteria pass. Link to CI runs / paste key output. Strategy: [standards/testing.md](../standards/testing.md).

## Current summary (2026-08-18)

| Suite | Command | Result |
|-------|---------|--------|
| Backend | `cd backend && DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test uv run --locked pytest -q` | **90 passed** |
| Frontend | `cd frontend && npm test` | **22 passed** |
| Lint / build | `uv run ruff check .` + `uv run ruff format --check .`; `npm run lint` + `npm run build` | clean |
| Supply chain | gitleaks; locked `pip-audit`; `npm audit --audit-level=high` | no findings |
| Runtime | Alembic downgrade/upgrade; production frontend headers; browser render/overlay check | pass |

> Includes durable rescore enqueue/status and null-score ordering regressions, scoring validation/error preservation, sortable-header accessibility, security-header configuration, Redis fail-closed/shared-rate-limit coverage, and frontend BFF credential-boundary tests. Historical snapshots are retained below.

### QA remediation — 2026-08-18

- Story: NEW-1…NEW-4, P1-8, P2-15, P3-23 — PASS
- Evidence: 90 backend tests; 22 frontend tests; Ruff and Next lint/build clean; migration `0005` downgrade/upgrade clean; production headers and browser content/error-overlay checks passed.
- Coverage: endpoint-specific validation messages, immediate contiguous-band validation, durable rescore enqueue/status/processing, scored/unscored ordering, accessible name/score header links, CSP/security headers, and one-shot migration startup.
- See: [qa_report_2026-08-18.md](qa_report_2026-08-18.md) §9.

## QA remediation summary (2026-07-27) — historical

At that checkpoint, 87 backend and 15 frontend tests passed. The detailed evidence entry below preserves the original commands and counts.

## MVP summary (2026-06-19) — historical

| Suite | Command | Result |
|-------|---------|--------|
| Backend | `cd backend && DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test pytest -q` | **66 passed** |
| Frontend | `cd frontend && npm test` | **6 passed** |
| Production smoke | `./scripts/deploy.sh` + `./scripts/rollback.sh` | Health green |

> Backend count includes 5 SSRF crawler tests added during the 2026-06-19 security-review hardening pass. Superseded by **Current summary (2026-07-27)** above.

---

## Template (per sprint)
```
### Sprint <n> / Phase <n> — <date>
- Story: <US-id> — <PASS|FAIL>
- Evidence: <CI link / command + output snippet>
- Coverage: <domain %, overall %>
```

---

### QA remediation — 2026-07-27
- Story: P0-1/P0-2, P1-3…P1-10, rate-limiter XFF bypass, fail-closed auth, frontend settings coverage — PASS
- Evidence:
  ```bash
  cd backend
  ruff check . && ruff format --check .
  DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test pytest -q
  # 87 passed

  cd frontend && npm test && npm run lint && npm run build
  # 15 passed; lint/build clean
  ```
- Coverage:
  - Crawl-failure retains signals (`test_qa_regressions` P0-1)
  - Scoring-config semantic validation (band names, gaps, full weights, bounds)
  - Operator `X-API-Key` + fail-closed empty key (`test_auth_fail_closed`)
  - Rate-limit not bypassable via forged `X-Forwarded-For`; entrypoint default pins empty trust
  - Discovery missing-key → `503 DISCOVERY_UNAVAILABLE` envelope
  - Filter enum/range 422s; `detected_at` on detail; LIKE escape
  - Frontend: scoring settings load/save/rescore, API helper coercion, list-query back-nav
- See: [qa_report_2026-07-27.md](qa_report_2026-07-27.md) §9

### LLM provider/config hardening — 2026-07-03
- Story: HTTP status handling / OpenAI base URL validation / LLM diagnostic CLI — PASS
- Evidence:
  ```bash
  cd backend
  ruff check .
  ruff format --check .
  DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test pytest -q
  # 66 passed
  ```
- Coverage: non-2xx LLM HTTP failures including redirects, transient retry statuses, settings-level OpenAI base URL validation, `dental-radar test-connection` success/failure exit codes.

### Security review hardening — 2026-06-19
- Story: SSRF guard / Gemini key / discover cap — PASS
- Evidence:
  ```bash
  cd backend && ruff check . && pytest tests/unit/test_website_crawler.py -v
  # 5 passed: scheme reject, metadata + loopback block, public allow, redirect-to-internal block
  ```
- Coverage: crawler scheme/IP denylist, per-hop redirect re-validation, header-based Gemini auth, `PLACES_MAX_PAGES` pagination cap.

### Sprint 7 / Phase 7 — 2026-06-19
- Story: US-G2 — PASS
- Evidence:
  ```bash
  cd backend && pytest tests/api/test_health.py -v
  # live + ready + legacy health

  cp .env.production.example .env.production  # edit secrets
  ./scripts/deploy.sh
  curl http://localhost:8000/api/v1/health/ready

  # CI: .github/workflows/deploy.yml (push to main)
  ```
- Coverage: multi-stage images, prod compose healthchecks, structured logs, backup script, rollback runbook + CI smoke.

### Sprint 6 / Phase 6 — 2026-06-19
- Story: US-F1, US-F2 — PASS
- Evidence:
  ```bash
  cd frontend && npm test
  # 6 passed (ClinicTable, FilterBar, detail breakdown)

  cd frontend && npm run build
  open http://localhost:3000/clinics
  ```
- Coverage: table rows, filter query params, score/AI breakdown rendering, loading/empty/error states.

### Sprint 5 / Phase 5 — 2026-06-19
- Story: US-E1, US-E2 — PASS
- Evidence:
  ```bash
  cd backend && pytest -v
  # 51 passed (includes live/ready health, enrichment, scoring, signals, discovery)

  curl -X POST http://localhost:8000/api/v1/clinics/{id}/enrich
  curl -X POST "http://localhost:8000/api/v1/clinics/{id}/enrich?force=true"

  python cli.py enrich --clinic-id <uuid>
  python cli.py enrich --all
  ```
- Coverage: schema clamp/truncate, repair-retry path, factory provider selection, skip-on-unchanged + force, list/detail growth_probability.

### Sprint 4 / Phase 4 — 2026-06-19
- Story: US-D1, US-D2, US-D3 — PASS
- Evidence:
  ```bash
  cd backend && pytest -v
  # 33 passed (9 scoring unit/API tests)

  curl -X POST http://localhost:8000/api/v1/clinics/{id}/score
  curl http://localhost:8000/api/v1/scoring-config
  curl -X PUT http://localhost:8000/api/v1/scoring-config -d '{"weights":{...},"bands":[...],"rescore":true}'

  python cli.py score --all
  ```
- Coverage: band boundaries, breakdown sum, config version bump + rescore, ranked list by score.

### Sprint 3 / Phase 3 — 2026-06-19
- Story: US-C1, US-C2 — PASS
- Evidence:
  ```bash
  cd backend && pytest -v
  # 21 passed (7 unit detector tests, 4 signal API/integration tests)

  curl -X POST http://localhost:8000/api/v1/clinics/{id}/signals:detect
  curl http://localhost:8000/api/v1/clinics/{id}/signals

  python cli.py detect --clinic-id <uuid>
  python cli.py detect --all
  ```
- Coverage: all 5 signal detectors, upsert/replace idempotency, weights from config, evidence persistence.

### Sprint 2 / Phase 2 — 2026-06-19
- Story: US-A1, US-A2, US-B1 — PASS
- Evidence:
  ```bash
  cd backend && pytest -v tests/api/test_clinics.py
  # 7 passed (upsert dedupe, discover endpoint, pagination, filters, detail, 404, Places mapping)

  curl -X POST http://localhost:8000/api/v1/clinics/discover \
    -H 'Content-Type: application/json' \
    -d '{"query":"dentist in Lisbon"}'
  # Requires GOOGLE_PLACES_API_KEY

  python cli.py discover --query "dentist in Lisbon"
  ```
- Coverage: discovery use case, repository upsert, list/get API, Google Places client mapping.

### Sprint 1 / Phase 1 — 2026-06-19
- Story: US-G1 — PASS
- Evidence:
  ```bash
  cd backend && ruff check . && ruff format --check . && pytest -v
  # 3 passed (test_health_returns_ok, test_all_tables_exist, test_scoring_config_v1_seeded)

  docker compose up --build -d
  curl http://localhost:8000/api/v1/health
  # {"status":"ok"}

  docker compose exec postgres psql -U dental_radar -d dental_radar \
    -c "SELECT version, active FROM scoring_config;"
  # version=1, active=t
  ```
- Coverage: domain stubs only (no domain logic yet); API + migration integration covered.
