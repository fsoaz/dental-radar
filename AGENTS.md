# Repository Guidelines

Dental Radar is a FastAPI/PostgreSQL backend (`backend/`) with a Next.js dashboard (`frontend/`). Read the canonical docs below rather than relying on this file for detail — it exists to route you and to carry the execution rules, which are not documented anywhere else.

## Canonical documentation

| Need | Read |
|------|------|
| Run, contribute, lint, test, host-mode development | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Python / TypeScript / git style | [docs/standards/conventions.md](docs/standards/conventions.md) |
| Test strategy, mocking, CI gates | [docs/standards/testing.md](docs/standards/testing.md) |
| REST conventions, error envelope, auth | [docs/standards/api_rules.md](docs/standards/api_rules.md) |
| LLM providers, prompts, retries | [docs/standards/ai_agent_rules.md](docs/standards/ai_agent_rules.md) |
| Layers, domain model, schema, pipeline | [docs/explanation/architecture.md](docs/explanation/architecture.md) |
| Every environment variable | [docs/reference/environment.md](docs/reference/environment.md) |
| Everything else | [docs/README.md](docs/README.md) |

## Non-negotiables

- **Dependency rule:** dependencies point inward. `domain/` imports nothing from `application/`, `infrastructure/`, or `presentation/`. Map SQLAlchemy models to entities at the repository boundary.
- **Docs in the same PR:** when behavior, a command, configuration, or an API contract changes, update the affected documentation in that PR.
- **Secrets:** never commit `.env`, `.env.production`, `frontend/.env.local`, API keys, or backups. Keep secret files mode `600`. Update the committed templates when configuration changes.
- **No paid external services from tests.** Google Places, crawlers, and LLM providers are mocked.
- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`, `test:`) with an imperative subject; branches `feat/…` or `fix/…`.

## Execution Rules

- Track work against the task budget and 15-hour project cap using recorded elapsed time and explicit estimates. Never infer or invent prior usage. If either limit is likely to be exceeded, stop and report completed work, remaining work, and the estimated overrun.
- Choose the simplest implementation that meets the acceptance criteria. Keep changes focused and proportional; do not build for hypothetical future requirements.
- Reuse existing code where appropriate. Add abstractions, layers, frameworks, dependencies, configuration, or extension points only when the task or an applicable architectural decision requires them.
- Refactor only what is necessary to complete the task. Capture unrelated improvement opportunities in review notes instead of implementing them.
- For every architectural change or new dependency, identify the requirement it satisfies and follow any applicable approval process.
- Preserve existing behavior unless the task requires a change. Add or update tests for every required behavior change.
- Preserve unrelated working-tree changes. Limit the final diff to the requested work and necessary supporting updates.
