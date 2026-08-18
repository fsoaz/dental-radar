# Run the pilot pipeline

Ingest clinics for a region, detect buying signals, score them, and enrich with an LLM. Then open the ranked list.

You need paid-provider keys for this path. For an empty stack with no keys, use [getting started](../tutorials/getting-started.md) first.

## Prerequisites

- Stack is up (`docker compose up`). See [getting started](../tutorials/getting-started.md).
- `GOOGLE_PLACES_API_KEY` set in `.env` (and therefore in compose).
- An LLM key for the configured `AI_PROVIDER` (`OPENAI_API_KEY` by default).
- **Python 3.12+** on the host if you use the CLI (compose API is already running).

> **Cost warning:** discovery and enrichment spend real money. Compose binds the stack to loopback; do not loosen that binding while paid-provider keys are set. See [troubleshoot](troubleshoot.md).

## Host CLI against compose Postgres

`.env.example` uses port `5432`. Compose publishes Postgres on **5433**. Export the compose URL before host CLI commands:

```bash
cd backend
export DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar
# Load the rest of .env (API keys) however you usually do, or copy values into the shell.
```

Command catalog: [CLI reference](../reference/cli.md).

## 1. Discover clinics

```bash
uv run --locked dental-radar discover --query "dentist in Lisbon"
```

Expected output shape:

```text
Ingested 60 clinics (48 created, 12 updated)
```

Discovery is capped at `PLACES_MAX_PAGES` (default 3 → 60 results) to bound spend.

Same job via the API (send `X-API-Key` when `API_KEY` is set):

```bash
curl -sS -X POST http://localhost:8000/api/v1/clinics/discover \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"query":"dentist in Lisbon"}'
```

The handler returns **200** with `ingested`, `created`, and `updated`. It runs synchronously.

## 2. Detect signals

```bash
uv run --locked dental-radar detect --all
```

Clinics without a website are skipped (`Clinic has no website`). Prior signals are retained when a crawl fails.

## 3. Score

```bash
uv run --locked dental-radar score --all
```

Each clinic gets a total, a [priority band](../reference/glossary.md), and a per-signal breakdown.

## 4. Test the LLM, then enrich

```bash
uv run --locked dental-radar test-connection
uv run --locked dental-radar enrich --all
```

Unchanged inputs are skipped (`Inputs unchanged`). Re-run with `--force` to overwrite.

## 5. Open the ranked list

Open http://localhost:3000/clinics. Filter to Hot / Immediate. Open a clinic for signals, score breakdown, and the AI explanation.

Tune weights at http://localhost:3000/settings/scoring — see [Tune scoring](tune-scoring.md).

## If a step fails

| Symptom | Where to look |
|---------|----------------|
| CLI cannot connect to Postgres | [Troubleshoot: wrong port](troubleshoot.md#backend-tests-or-cli-cannot-reach-postgres) |
| `503` `API_KEY_NOT_CONFIGURED` | [Troubleshoot: API key](troubleshoot.md#mutating-route-returns-503-api_key_not_configured) |
| `429` `DISCOVERY_QUOTA_EXCEEDED` | Google Places quota; wait or lower `PLACES_MAX_PAGES` |
| `502` `DISCOVERY_UNAUTHORIZED` | Bad or missing `GOOGLE_PLACES_API_KEY` |
| `502` `ENRICHMENT_FAILED` | LLM key, model, or `OPENAI_BASE_URL`; run `test-connection` |
