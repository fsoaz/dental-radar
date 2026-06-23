# Repository Guidelines

## Project Structure & Module Organization

`backend/app/` follows Clean Architecture: `domain/` contains business logic; `application/` contains use cases and ports; `infrastructure/` contains database and external adapters; and `presentation/` exposes FastAPI routes. Backend tests are under `backend/tests/{unit,integration,api}`. The Next.js application lives in `frontend/app/`, with reusable components in `frontend/components/`, API helpers in `frontend/lib/`, tests in `frontend/tests/`, and assets in `frontend/public/`. Documentation lives in `docs/`; deployment utilities live in `scripts/`.

## Build, Test, and Development Commands

- `docker compose up --build`: start PostgreSQL, API, and dashboard locally.
- `cd backend && pip install -e ".[dev]"`: install backend and development tools.
- `cd backend && alembic upgrade head`: apply database migrations.
- `cd backend && uvicorn app.main:app --reload`: run the API on port 8000.
- `cd backend && ruff check . && ruff format --check . && pytest`: lint, format-check, and test the backend.
- `cd frontend && npm ci && npm run dev`: install locked dependencies and run the dashboard on port 3000.
- `cd frontend && npm run lint && npm test && npm run build`: validate, test, and production-build the frontend.

## Coding Style & Naming Conventions

Python targets 3.12, uses four-space indentation, type hints, Ruff formatting, double quotes, and a 100-character line limit. Use `snake_case` for modules/functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Domain and application code must not import infrastructure or presentation concerns.

TypeScript is strict and ESLint-checked. Use `PascalCase` components, `camelCase` functions and variables, and `kebab-case.tsx` filenames. Keep API access in `frontend/lib/api.ts` and styling in Tailwind utilities.

## Testing Guidelines

Use pytest for backend tests and Vitest with React Testing Library for frontend components. Name tests `test_*.py` or `*.test.tsx`, matching the layer under test. Mock Google Places, crawlers, and LLM providers; CI must not call live external services. Prioritize scoring boundaries, signal detection, API contracts, and filtering behavior. Target roughly 90% coverage for domain services and 70% overall backend coverage.

## Commit & Pull Request Guidelines

Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`) with imperative subjects under 50 characters. Use branches such as `feat/...` or `fix/...`. Keep PRs focused, explain behavior and verification, link relevant issues, and include screenshots for UI changes. All lint, test, and build checks must pass before merging to `main`.

## Security & Configuration

Copy committed `.env.example` files for local setup; never commit `.env`, `.env.local`, production secrets, or API keys. Keep environment templates current when adding configuration.
