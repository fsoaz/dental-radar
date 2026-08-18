# Contributing

How to change Dental Radar. Product and architecture: [docs/README.md](docs/README.md). Style: [conventions](docs/standards/conventions.md).

## Prerequisites

- **Python 3.12+** (CI uses 3.12)
- **Node 22** (CI uses 22)
- Docker Compose (Postgres on host port **5433**)
- Create `.env` with `install -m 600 .env.example .env` before running the stack

## Workflow

1. Branch from `main`: `feat/…`, `fix/…`, `chore/…`, or `docs/…`.
2. Make the change. If behavior or a public command changes, update the docs **in the same PR**.
3. Lint and test locally (commands below).
4. Open a PR. CI (`.github/workflows/ci.yml`) must pass before merge.

Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`). Imperative subject, about 50 characters.

## Backend

```bash
cd backend
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
```

Install the pre-commit hook once so ruff runs before push:

```bash
uv tool install pre-commit
pre-commit install
```

Integration and API tests need Postgres and a test database:

```bash
docker compose up -d postgres
docker compose exec postgres createdb -U dental_radar dental_radar_test
cd backend
DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar_test uv run --locked pytest
```

If `createdb` says the database exists, continue. Wrong port: [troubleshoot](docs/how-to/troubleshoot.md).

## Frontend

```bash
cd frontend
install -m 600 .env.example .env.local
npm ci
npm run lint
npm test
npm run build
```

This project uses Next.js 15 with React 19. Run `npm audit --audit-level=high` before submitting dependency changes; CI enforces the same high/critical gate. Do not run `npm audit fix --force` or use `--legacy-peer-deps`: make compatible, reviewed updates and commit the resulting lockfile.

## Documentation

Docs live in `docs/` (Markdown) plus this file, [CHANGELOG.md](CHANGELOG.md), and the root [README.md](README.md).

- Match the hub sections: tutorial, how-to, explanation, reference.
- Verify commands against the current code. Do not document from memory.
- Keep examples copy-paste runnable. Mark anything that is not.
- Internal engineering notes stay under [docs/internal/](docs/internal/README.md).

## Secrets

Do not commit `.env`, `.env.production`, `frontend/.env.local`, or files under `backups/`.
Keep local secret files mode `600`; the setup commands above create them with that mode.
