# REST API Rules

Conventions for the FastAPI backend. Endpoint catalog in [architecture.md → API design](../explanation/architecture.md#6-api-design-deliverable-5). Narrative request examples: [reference/api.md](../reference/api.md).

## Versioning & base
- Base path `/api/v1`. Breaking changes → `/api/v2`.

## Resource naming
- Plural nouns: `/clinics`, `/signals`, `/scoring-config`.
- Sub-resources: `/clinics/{id}/signals`.
- Actions that aren't CRUD use a verb suffix with `:`: `/clinics/{id}/signals:detect`, or a clear POST sub-path (`/clinics/{id}/enrich`).

## Methods & status codes
| Action | Method | Success |
|--------|--------|---------|
| List | GET | 200 |
| Read | GET | 200 (404 if missing) |
| Create | POST | 201 (Location header) |
| Trigger job | POST | 202 (async) or 200 (sync) |
| Update/replace | PUT | 200, or 202 when it also queues async work |
| Delete | DELETE | 204 |
| Health (live) | GET | 200 |
| Health (ready) | GET | 200 when DB answers `SELECT 1` |

**MVP exception:** discover, detect, score, and enrich are synchronous and return **200**, not 201/202. There is no 201 Location for discovery (upsert by `place_id`).

`PUT /scoring-config` returns **202** only when `rescore=true`; the response includes a durable `rescore_job` handle. Poll `GET /scoring-config/rescore-jobs/{id}` until `succeeded` or `failed`.

- Validation error → **422** (`VALIDATION_ERROR` envelope, or FastAPI field errors in `details`).
- Auth missing/invalid → **401** (`UNAUTHORIZED`); missing `API_KEY` config → **503** (`API_KEY_NOT_CONFIGURED`).
- Rate limited → **429** (`RATE_LIMITED`).
- Conflict (dup `place_id`) → **409**.
- Conflict (concurrent `PUT /scoring-config` write) → **409** (`SCORING_CONFIG_CONFLICT`); safe to retry.
- Discovery upstream unavailable → **503** (`DISCOVERY_UNAVAILABLE`); quota → **429**; bad Places key → **502**.
- Enrichment LLM failure → **502** (`ENRICHMENT_FAILED`).
- Server error → **500** (`INTERNAL_ERROR`, request id in `details`; no stack trace in body).

## Health endpoints
| Path | Purpose |
|------|---------|
| `GET /health/live` | Liveness — no DB check |
| `GET /health/ready` | Readiness — verifies DB connectivity |
| `GET /health` | Legacy alias for readiness |

Orchestrators should use `/health/ready` after deploy; use `/health/live` for process restarts only.

`GET /health/ready` returns 200 `{ "status": "ok" }` when `SELECT 1` succeeds. If the database is unreachable, the handler does not catch the error; the generic **500** `INTERNAL_ERROR` path runs. Legacy `GET /health` catches DB errors and returns **503** `{ "status": "degraded" }`.

## Error envelope
```json
{
  "error": {
    "code": "CLINIC_NOT_FOUND",
    "message": "Clinic f0c9... not found",
    "details": null
  }
}
```
`code` is a stable machine string; `message` human-readable; `details` optional object (e.g. field errors).

## Pagination
- Query params `page` (1-based), `page_size` (default 20, max 100).
- List responses wrap data:
```json
{ "data": [ ... ], "page": 1, "page_size": 20, "total": 142 }
```

## Filtering & sorting
- Filters are explicit query params (`state`, `priority`, `min_score`, `signal_type`, `has_website`).
- Sort via `sort` param; `-` prefix = descending (`sort=-score`). Default `-score` for `/clinics`.

## Request/response
- JSON only. `snake_case` keys.
- Request validation via Pydantic schemas in `presentation/api/v1/schemas/`. Never bind raw ORM models to responses — use response schemas/DTOs.
- Timestamps ISO-8601 UTC.

## Auth
- **Operator API key (MVP):** mutating/paid routes require header `X-API-Key` matching env `API_KEY`:
  - `POST /clinics/discover`
  - `POST /clinics/{id}/signals:detect`
  - `POST /clinics/{id}/score`
  - `POST /clinics/{id}/enrich`
  - `PUT /scoring-config`
- **Fail closed:** if `API_KEY` is empty, those routes return **503** `API_KEY_NOT_CONFIGURED` unless `ALLOW_UNAUTHENTICATED=true` (local/test escape hatch only). Do not rely on `APP_ENV` alone.
- GET routes (list/detail/signals/config/health) remain open for the dashboard.
- Per-user authentication remains **post-MVP**; no JWT/login scaffolding is shipped.
- Still bind production API to loopback / internal network (see [deploy.md](../how-to/deploy.md) pre-flight). In-app rate limits cover discover, enrich, detect, and mutating `PUT /scoring-config`. Read-only `GET` routes and `POST /clinics/{id}/score` are not rate-limited.

## Outbound requests (SSRF)
- Server-side fetches to clinic-controlled URLs (crawler) go through the SSRF guard: `http`/`https` only, DNS resolved against a private/link-local/metadata denylist, redirects followed manually with per-hop re-validation. The resolved IP is pinned for the actual request (Host header + SNI preserved) so a DNS-rebind between validation and connect can't slip through. Any new outbound fetch from user-controlled input must reuse this guard.
- Discovery pagination is bounded by `PLACES_MAX_PAGES` to cap paid third-party API usage.

## Idempotency
- Discovery upserts by `place_id` (re-run safe).
- Signal detection on **success** replaces the clinic's signal set. On **crawl failure** or missing website, prior signals are **retained** (no empty write).
- Scoring/enrichment overwrite the single row per clinic.

## Docs
- OpenAPI at `/docs` (Swagger) and `/openapi.json` in non-production only.
- When `APP_ENV=production`, `/docs`, `/redoc`, and `/openapi.json` are disabled (404).
