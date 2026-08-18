# Environment variables

Single catalog. Templates: [`.env.example`](../../.env.example), [`.env.production.example`](../../.env.production.example), [`frontend/.env.example`](../../frontend/.env.example). Python defaults: [`settings.py`](../../backend/app/infrastructure/config/settings.py).

Never commit `.env`, `.env.production`, or `frontend/.env.local`.

## Which file

| File | Use |
|------|-----|
| `.env` | Local compose / host API (gitignored) |
| `.env.example` | Dev template (committed) |
| `.env.production` | Production secrets (gitignored) |
| `.env.production.example` | Production template (committed) |
| `frontend/.env.local` | Host Next.js overrides |

Compose injects API variables from the root `.env`. Browser requests use the same-origin Next.js BFF; secrets remain server-side at runtime.

## Local / API (`.env.example`)

| Variable | Default / example | Purpose |
|----------|-------------------|---------|
| `DATABASE_URL` | `postgresql://dental_radar:dental_radar@localhost:5432/dental_radar` | SQLAlchemy URL. Compose Postgres on the **host** is port **5433**. |
| `API_KEY` | empty | Operator key. Send as `X-API-Key`. Empty + `ALLOW_UNAUTHENTICATED=false` → **503**. |
| `ALLOW_UNAUTHENTICATED` | `true` in `.env.example`; **`false` in settings** | Local/test escape hatch. Compose also defaults `true`. |
| `RATE_LIMIT_PER_MINUTE` | `30` | In-app limiter. Local compose often sets `60`. |
| `REDIS_URL` | `redis://localhost:6379/0` | Shared rate-limit store. Limited routes fail closed if unavailable. |
| `RATE_LIMIT_TRUSTED_PROXIES` | empty | Proxy IPs/CIDRs whose `X-Forwarded-For` may set the client key. Empty = trust none. |
| `FORWARDED_ALLOW_IPS` | empty | uvicorn `X-Forwarded-*` trust list. Keep in sync with `RATE_LIMIT_TRUSTED_PROXIES`. |
| `GOOGLE_PLACES_API_KEY` | empty | Discovery. Leave unset until you ingest. |
| `PLACES_MAX_PAGES` | `3` | Max Places pages per query (20 results/page). |
| `AI_PROVIDER` | `gpt` | `gpt` \| `claude` \| `gemini`. |
| `AI_FALLBACK_PROVIDER` | empty | Second provider after primary retries fail. Same name as primary is ignored. |
| `AI_RETRY_MAX` | `3` | Transient LLM retries (exponential backoff). |
| `AI_MAX_SITE_TEXT_CHARS` | `8000` | Truncate crawled site text before the prompt. |
| `OPENAI_API_KEY` | empty | GPT / OpenAI-compatible. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Must be `https://` when GPT is primary or fallback. Blank falls back to OpenAI. |
| `OPENAI_MODEL` | `gpt-4o-mini` | GPT model id. |
| `ANTHROPIC_API_KEY` | empty | Claude. |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Claude model id. |
| `GEMINI_API_KEY` | empty | Gemini. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model id. |
| `CORS_ORIGINS` | localhost variants on 3000/3001 | Comma-separated browser origins. Production: public frontend origin only. |
| `LOG_LEVEL` | `INFO` | |
| `LOG_JSON` | `true` in example; compose local often `false` | Structured request logs. |
| `APP_ENV` | `development` | `production` disables `/docs`, `/redoc`, `/openapi.json`. |

Settings also accept (not in `.env.example`; defaults in code):

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_TIMEOUT_SECONDS` | `60` | LLM HTTP timeout. |
| `CRAWLER_TIMEOUT_SECONDS` | `10` | Clinic website fetch timeout. |

## Production extras (`.env.production.example`)

| Variable | Purpose |
|----------|---------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Compose Postgres. Changing the password on an existing volume does not update the role automatically. |
| `API_BIND` | Default `127.0.0.1`. Use `0.0.0.0` only behind a trusted edge. |
| `FRONTEND_BIND` | Default `127.0.0.1`. The BFF grants write access, so expose only through an operator-only edge. |
| `API_PORT` / `FRONTEND_PORT` | Host publish ports. |
| `GITHUB_REPOSITORY` / `IMAGE_TAG` | GHCR image coordinates for `scripts/deploy.sh`. |
| `API_IMAGE` / `FRONTEND_IMAGE` | Optional full image overrides. |

Production compose requires `POSTGRES_PASSWORD` and `API_KEY`. It forces `ALLOW_UNAUTHENTICATED=false`.

## Frontend (`frontend/.env.example`)

| Variable | Purpose |
|----------|---------|
| `API_URL` | Server-side fetch base inside the Next.js container (compose sets `http://api:8000/api/v1`). |
| `API_KEY` | Server-only key injected by the BFF on mutating requests. Never exposed to browser JavaScript. |

## Local vs production posture

- Local compose: all published ports bind `127.0.0.1`; `ALLOW_UNAUTHENTICATED=true` remains a local-only convenience.
- Production: [deploy pre-flight](../how-to/deploy.md#pre-flight-security).
