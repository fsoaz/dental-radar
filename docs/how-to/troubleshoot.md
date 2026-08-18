# Troubleshoot

Fixes for the failures that show up first. API error codes: [API reference](../reference/api.md). Env vars: [environment](../reference/environment.md).

## Backend tests or CLI cannot reach Postgres

**Symptoms**

- `pytest` fails with a connection error, or "database dental_radar_test does not exist".
- Host `python cli.py …` fails with `connection refused` on port `5432`.

**Why**

Compose maps Postgres as `5433:5432`. `.env.example` still uses `5432`. Host processes must use **5433**. The test database is not created automatically.

**Fix**

```bash
docker compose up -d postgres
docker compose exec postgres createdb -U dental_radar dental_radar_test
```

Run tests with the compose port:

```bash
cd backend
DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test uv run --locked pytest
```

Run the CLI against the compose database:

```bash
cd backend
export DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar
uv run --locked dental-radar discover --query "dentist in Lisbon"
```

If you run Postgres yourself on the host at `5432`, keep `5432` and skip the compose mapping.

## Mutating route returns 503 `API_KEY_NOT_CONFIGURED`

**Symptoms**

```json
{"error":{"code":"API_KEY_NOT_CONFIGURED","message":"API_KEY is not configured. Set API_KEY, or ALLOW_UNAUTHENTICATED=true for local/test only.","details":null}}
```

Status **503**. Affects `POST /clinics/discover`, `POST /clinics/{id}/signals:detect`, `POST /clinics/{id}/score`, `POST /clinics/{id}/enrich`, and `PUT /scoring-config`.

**Why**

`API_KEY` is empty and `ALLOW_UNAUTHENTICATED` is `false`. Auth fails closed even when `APP_ENV=development`. Compose defaults `ALLOW_UNAUTHENTICATED=true`; a host `uvicorn` process using `.env` only does **not**, unless you set the flag.

**Fix**

- Local compose: keep `ALLOW_UNAUTHENTICATED=true` in `docker-compose.yml`, or set `API_KEY` in `.env` and send `X-API-Key`.
- Host API: `export ALLOW_UNAUTHENTICATED=true` for local-only, or set `API_KEY` and send the header.
- Production: set a non-empty `API_KEY` and leave `ALLOW_UNAUTHENTICATED=false`. See [deploy pre-flight](deploy.md#pre-flight-security).

A present but wrong key returns **401** `UNAUTHORIZED`, not 503.

## Dashboard mutation returns 503 `BFF_NOT_CONFIGURED`

**Why**

The browser sends writes to the same-origin `/api/backend` proxy. That server-side proxy fails closed unless both `API_URL` and `API_KEY` are configured for the frontend process. The operator key is intentionally never stored in browser `localStorage` or exposed through a `NEXT_PUBLIC_*` variable.

**Fix**

- Compose: set a non-empty `API_KEY` in the root `.env`; Compose supplies the same key to the API and frontend containers.
- Host frontend: copy `frontend/.env.example` to `frontend/.env.local`, then set `API_URL=http://localhost:8000/api/v1` and the same `API_KEY` used by the backend.
- Restart the frontend after changing its environment.

## Rate-limited route returns 503 `RATE_LIMIT_UNAVAILABLE`

**Symptoms**

Mutating discovery, enrichment, signal detection, or scoring-config requests return 503.

**Why**

Redis is unavailable, so the API fails closed rather than silently removing shared cost controls.

**Fix**

- Run `docker compose ps redis` and `docker compose logs redis`.
- Confirm `REDIS_URL` points to `redis://redis:6379/0` inside Compose or the correct external Redis endpoint.
- Restore Redis; do not bypass the limiter for availability.

## Dashboard shows an empty list or stale data after ingest

**Symptoms**

CLI printed ingested clinics; http://localhost:3000/clinics is empty or still loading.

**Why**

The browser calls the same-origin `/api/backend` proxy. The Next.js server uses `API_URL`; a host `npm run dev` with a wrong `.env.local` can point the proxy at the wrong API. The list also stays empty until discovery has run.

**Fix**

- Confirm `curl -fsS http://localhost:8000/api/v1/clinics` returns `"total"` greater than 0.
- For host Next.js, set `API_URL=http://localhost:8000/api/v1` and `API_KEY` in `frontend/.env.local` (see `frontend/.env.example`).
- Hard-refresh the browser.

## `/docs` returns 404

**Why**

OpenAPI is disabled when `APP_ENV=production` (`/docs`, `/redoc`, `/openapi.json` all 404).

**Fix**

Use local compose (`APP_ENV=development`) or read [API reference](../reference/api.md). Do not enable Swagger on a public production API.

## Rate limited (429 `RATE_LIMITED`)

Default is `RATE_LIMIT_PER_MINUTE` (settings default **30**; local compose often **60**). Limits apply to discover, mutating `PUT /scoring-config`, paths ending in `/signals:detect`, and paths ending in `/enrich`. Read-only `GET` routes and `POST /clinics/{id}/score` are not rate-limited.

Wait for the window, or raise the env var in local only.

Redis-backed counters are shared by every API replica. `Retry-After` reports the remaining bucket lifetime.
