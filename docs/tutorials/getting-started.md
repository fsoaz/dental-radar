# Getting started

Bring the stack up and open an empty dashboard in under 10 minutes. You do not need Google Places or LLM keys for this path.

## Prerequisites

- Docker and Docker Compose
- A clone of this repository

Host-run API/CLI later needs **Python 3.12+**. Host-run dashboard later needs **Node 22**. Compose is enough for this tutorial.

## 1. Copy the env template

From the repository root:

```bash
install -m 600 .env.example .env
```

Leave `GOOGLE_PLACES_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GEMINI_API_KEY` empty. You are not ingesting yet.

The empty `API_KEY` is enough for this read-only walkthrough. Before using dashboard actions that mutate data, set a local operator key in `.env` and restart the stack; the same value is supplied server-side to both the API and frontend proxy.

## 2. Start the stack

```bash
docker compose up --build
```

Wait until the API healthcheck is green. Compose maps Postgres to host port **5433** (`5433:5432`).

## 3. Confirm the API is ready

```bash
curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready
```

Expected body:

```json
{"status":"ok"}
```

Open the generated OpenAPI UI at http://localhost:8000/docs — it is available because compose sets `APP_ENV=development`.

## 4. Open the dashboard

Open http://localhost:3000/clinics.

The list is empty until you ingest clinics. Scoring settings live at http://localhost:3000/settings/scoring.

## What you have running

| Service | Host |
|---------|------|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Postgres | `localhost:5433` |
| Redis | internal Compose network only |

> **Warning:** compose keeps `ALLOW_UNAUTHENTICATED=true` for local development but binds every published service to `127.0.0.1`. Do not loosen that binding while paid-provider keys are configured. Details: [troubleshoot](../how-to/troubleshoot.md).

## Next

- Ingest a region: [Run the pilot pipeline](../how-to/run-pilot-pipeline.md)
- Change weights: [Tune scoring](../how-to/tune-scoring.md)
- Run tests on the host: [CONTRIBUTING.md](../../CONTRIBUTING.md)
