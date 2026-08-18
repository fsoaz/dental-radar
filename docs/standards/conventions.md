# Coding Conventions

Applies to backend (Python) and frontend (TypeScript). Keep it simple — MVP over enterprise.

## Python (backend)
- **Version:** 3.12+. **Style:** `ruff` (lint) + `ruff format`. Line length 100.
- **Typing:** full type hints; `mypy` in CI (non-blocking warning at MVP).
- **Naming:** `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` consts, modules `snake_case`.
- **Architecture rule:** Domain imports nothing from `infrastructure`/`presentation`. Enforced by review (optionally `import-linter`).
- **Use cases:** one class/function per use case, single `execute()` entry. No framework imports in domain/application.
- **Errors:** raise domain exceptions (`ClinicNotFound`, `EnrichmentFailed`) in inner layers; map to HTTP in presentation only.
- **Config:** `pydantic-settings`; all config from env. No secrets in code. `.env.example` kept current.
- **IDs:** UUID v4 primary keys. Timestamps `timestamptz`, UTC.
- **Dependencies:** managed in `pyproject.toml`.
- **Logging:** JSON structured logs when `LOG_JSON=true`; request middleware adds `X-Request-ID`.

## TypeScript (frontend)
- **Style:** ESLint (`next lint`). Strict TS (`strict: true`).
- **Naming:** `PascalCase` components, `camelCase` vars/functions, files `kebab-case.tsx`.
- **Data fetching:** typed API client in `lib/api.ts`; components use fetch helpers, not scattered raw URLs.
- **Styling:** Tailwind utility-first; shared UI via shadcn-style components in `components/ui/`.
- **State:** URL search params for list filters; client fetch for API data in MVP.

## Git
- **Branches:** `feat/…`, `fix/…`, `chore/…`, `docs/…`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`). Subject ≤ 50 chars, imperative.
- **PRs:** small, one concern; must pass CI (lint + tests) before merge to `main`. Deploy workflow runs on merge to `main`.

## Project layout rules
- Backend follows the tree in [architecture.md → Folder structure](../explanation/architecture.md#7-folder-structure-deliverable-6). Don't leak SQLAlchemy models into domain — map at the repository boundary.
- One module = one responsibility (SOLID-S).

## Environment & config

| File | Use |
|------|-----|
| `.env` | Local dev (gitignored) |
| `.env.example` | Dev template (committed) |
| `.env.production` | Production secrets (gitignored) |
| `.env.production.example` | Production template (committed) |
| `frontend/.env.local` | Next.js local overrides |

Catalog of every variable: [environment.md](../reference/environment.md). Keep `.env.example` and `.env.production.example` in sync with that page.
Create secret-bearing env files with mode `600` (for example, `install -m 600 .env.example .env`).

**Local stacks:**
- Dev: `docker compose up` (Postgres on host port **5433**). Every published service binds to `127.0.0.1`; keep that boundary while `ALLOW_UNAUTHENTICATED=true` or paid-provider keys are configured.
- Prod: `docker compose -f docker-compose.prod.yml up -d` after configuring `.env.production`

`CORS_ORIGINS` defaults narrowly in Python settings. Keep broad localhost/0.0.0.0 origin lists in dev-only templates/compose files; production must set only trusted public frontend origins.
