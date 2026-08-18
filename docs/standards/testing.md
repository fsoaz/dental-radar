# Testing Strategy

Pragmatic MVP testing — cover the logic that matters (scoring, signal rules, ingestion), mock the expensive externals.

**Current verified counts (2026-08-17):** 88 backend (`pytest`), 17 frontend (`vitest`). Recount after adding tests. Evidence: [test_evidence.md](../internal/test_evidence.md).

## Backend (pytest)

Layered, matching Clean Architecture:

| Layer | What | Style |
|-------|------|-------|
| **Unit (domain)** | `ScoringService`, `SignalDetectionService`, value objects, band mapping, enrichment parser | pure, no I/O, fast |
| **Integration (infra)** | SQLAlchemy repos, migrations, Google Places client, crawler, LLM factory | real Postgres (test DB), externals mocked |
| **API contract** | routers via `TestClient` | spin app, hit `/api/v1`, assert status + schema |

### Priorities (must-have coverage)
- Scoring: weights sum correctly, band thresholds at boundaries (50/51, 100/101, 150/151), breakdown sums to total.
- Config-driven scoring: changing weights/bands changes result without code change.
- Discovery upsert: same `place_id` updates, no duplicate.
- Signal detection: each detector fires on known evidence, ignores absent evidence.
- Enrichment: schema clamp/truncate, repair-retry, skip-on-unchanged, fake provider in API tests.
- Health: live, ready, legacy `/health`.
- API: list filters/sort/pagination; 404 paths.
- Crawler SSRF guard: rejects non-http(s) schemes, private/loopback/metadata IPs, and redirects to internal addresses.

## Mocking externals
- **Google Places:** `FakeClinicSource` in tests. No live API in CI.
- **Website crawler:** static HTML fixtures per signal scenario (`FakeWebsiteCrawler`).
- **LLM providers:** `FakeLLMProvider` returning canned `EnrichmentResult`; factory tested by env. No live LLM calls in CI.

## Fixtures
- `pytest` fixtures: test DB session (rolled back per test), seeded `scoring_config` v1, sample clinics, sample HTML.
- Test DB URL: `postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test` (compose port 5433).
- Create the test DB once with `docker compose exec postgres createdb -U dental_radar dental_radar_test`.

## Frontend
- **Unit/component:** Vitest + React Testing Library — `ClinicTable`, `FilterBar`, score/AI breakdown.
- **E2E:** Playwright happy path — not yet in CI.

## Coverage targets (MVP)
- Domain services: ~90%.
- Overall backend: ~70%. Don't chase 100% on glue/infra.

## CI

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` | PR + push to `main` | gitleaks; backend locked install + ruff + pytest + pip-audit; frontend `npm ci` + eslint + vitest + high/critical audit gate |
| `deploy.yml` | push to `main` | same security/test gate → build/push GHCR images → smoke deploy + rollback |

Dependabot monitors both package ecosystems. Green CI is required to merge, and deploy images are not published unless the gate passes. Test evidence is summarized in [test_evidence.md](../internal/test_evidence.md) per sprint.
