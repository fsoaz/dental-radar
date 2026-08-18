# CLI

Batch pipeline commands. Source: [`backend/cli.py`](../../backend/cli.py). After `uv sync --locked --extra dev`, run them as `uv run dental-radar` or `uv run python cli.py`.

## Prerequisites

- **Python 3.12+**
- `DATABASE_URL` pointing at Postgres. Compose publishes **5433** on the host — see [troubleshoot](../how-to/troubleshoot.md).
- `GOOGLE_PLACES_API_KEY` for `discover`
- An LLM key for `enrich` and `test-connection` (`OPENAI_API_KEY` when `AI_PROVIDER=gpt`)

From the `backend/` directory:

```bash
export DATABASE_URL=postgresql://dental_radar:dental_radar@localhost:5433/dental_radar
uv run dental-radar --help
```

## Commands

### `discover`

```bash
uv run dental-radar discover --query "dentist in Lisbon"
```

`--query` is required. Upserts clinics from Google Places. Prints ingested / created / updated counts. Capped by `PLACES_MAX_PAGES`.

### `detect`

```bash
uv run dental-radar detect --clinic-id 11111111-1111-4111-8111-111111111111
uv run dental-radar detect --all
```

`--clinic-id` and `--all` are mutually exclusive; one is required. Crawls each clinic website and writes signals. Clinics with no website are skipped; the CLI prints `Note: …`.

### `score`

```bash
uv run dental-radar score --clinic-id 11111111-1111-4111-8111-111111111111
uv run dental-radar score --all
```

Uses the active scoring config. Per-clinic output includes total, priority band, and config version.

### `enrich`

```bash
uv run dental-radar enrich --clinic-id 11111111-1111-4111-8111-111111111111
uv run dental-radar enrich --all
uv run dental-radar enrich --clinic-id 11111111-1111-4111-8111-111111111111 --force
```

`--force` re-enriches even when inputs are unchanged. Without it, unchanged clinics print `Skipped clinic …: Inputs unchanged`.

### `test-connection`

```bash
uv run dental-radar test-connection
```

Sends a canned clinic payload to the configured LLM provider. Use this before `enrich --all`. Exit code 1 on failure; prints provider error details to stderr.

## End-to-end

Operator walkthrough: [run the pilot pipeline](../how-to/run-pilot-pipeline.md). HTTP equivalents: [API](api.md).
