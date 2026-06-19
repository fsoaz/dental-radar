# REST API Rules

Conventions for the FastAPI backend. Endpoint catalog in [architecture.md → API design](../context/architecture.md#6-api-design-deliverable-5).

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
| Update/replace | PUT | 200 |
| Delete | DELETE | 204 |
| Health (live) | GET | 200 |
| Health (ready) | GET | 200 (503 if DB down) |

- Validation error → **422** (FastAPI/Pydantic default).
- Auth missing/invalid → **401**; forbidden → **403** *(auth not implemented in MVP)*.
- Conflict (dup `place_id`) → **409**.
- Enrichment LLM failure → **502** (`ENRICHMENT_FAILED`).
- Server error → **500** (no stack trace in body).

## Health endpoints
| Path | Purpose |
|------|---------|
| `GET /health/live` | Liveness — no DB check |
| `GET /health/ready` | Readiness — verifies DB connectivity |
| `GET /health` | Legacy alias for readiness |

Orchestrators should use `/health/ready` after deploy; use `/health/live` for process restarts only.

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
- JWT bearer (`Authorization: Bearer <token>`) planned for post-MVP. `POST /auth/login` not yet implemented — API is open in MVP.
- Because the API is open, mutating/expensive routes (`PUT /scoring-config`, `POST /clinics/discover|{id}/enrich|{id}/signals:detect`) MUST be shielded by network isolation (internal-only binding, reverse proxy + VPN/IP allowlist) and edge rate limiting until auth ships.

## Outbound requests (SSRF)
- Server-side fetches to clinic-controlled URLs (crawler) go through the SSRF guard: `http`/`https` only, DNS resolved against a private/link-local/metadata denylist, redirects followed manually with per-hop re-validation. Any new outbound fetch from user-controlled input must reuse this guard.
- Discovery pagination is bounded by `PLACES_MAX_PAGES` to cap paid third-party API usage.

## Idempotency
- Discovery upserts by `place_id` (re-run safe). Signal detection replaces same-type signals per clinic. Scoring/enrichment overwrite the single row per clinic.

## Docs
- OpenAPI auto-served at `/docs` (Swagger) and `/openapi.json`.
