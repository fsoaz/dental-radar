# Dental Radar

B2B sales-intelligence platform that ranks dental clinics by purchase propensity.

It answers one question: **which clinics should a salesperson contact first?**

## Install

Prerequisites:

- Docker and Docker Compose
- **Python 3.12+** if you run the API or CLI on the host (CI uses 3.12)
- **Node 22** if you run the dashboard on the host (CI uses 22)

```bash
install -m 600 .env.example .env
docker compose up --build
```

Local compose sets `ALLOW_UNAUTHENTICATED=true` and binds every published port to loopback. Set `API_KEY` before using dashboard write actions: the frontend proxy injects it server-side and fails closed when it is empty. Leave `GOOGLE_PLACES_API_KEY` and LLM keys unset until you ingest.

Compose Postgres is on host port **5433** (`5433:5432`).

## Run

After `docker compose up --build`:

| What | URL |
|------|-----|
| Dashboard | http://localhost:3000/clinics |
| Scoring settings | http://localhost:3000/settings/scoring |
| API readiness | http://localhost:8000/api/v1/health/ready |
| API docs (Swagger) | http://localhost:8000/docs (disabled when `APP_ENV=production`) |

Next steps:

- [Getting started](docs/tutorials/getting-started.md) — empty dashboard in under 10 minutes, no paid keys
- [Run the pilot pipeline](docs/how-to/run-pilot-pipeline.md) — discover → detect → score → enrich
- [Documentation hub](docs/README.md) — tutorials, how-tos, reference, architecture

The development stack is reachable only from the local machine. Keep that loopback binding if paid-provider keys are configured.

**Production:** [deploy](docs/how-to/deploy.md) and [rollback](docs/how-to/rollback.md). Copy `.env.production.example` to `.env.production`, complete the security pre-flight, then `./scripts/deploy.sh`.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for lint, tests, the test database, and the docs-in-the-same-PR rule. Human-readable history: [CHANGELOG.md](CHANGELOG.md).
