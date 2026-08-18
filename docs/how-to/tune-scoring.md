# Tune scoring

Change signal weights and priority bands without a redeploy. The next score run (or `rescore=true` on the config update) re-ranks clinics.

Concepts: [glossary](../reference/glossary.md) · engine: [architecture → scoring](../explanation/architecture.md#3-scoring-engine--configuration).

## Prerequisites

- Stack is up. See [getting started](../tutorials/getting-started.md).
- The dashboard is reachable only through the trusted operator network boundary.

Default weights and bands (seeded `scoring_config` v1):

| Signal | Default weight |
|--------|---------------:|
| `HIRING` | 25 |
| `ADVERTISING` | 30 |
| `WEBSITE_QUALITY` | 15 |
| `MULTI_LOCATION` | 40 |
| `HIGH_TICKET` | 20 |

| Band | Score range |
|------|-------------|
| `COLD` | 0–50 |
| `WARM` | 51–100 |
| `HOT` | 101–150 |
| `IMMEDIATE` | 151+ |

## Option A — dashboard

1. Open http://localhost:3000/settings/scoring.
2. Edit weights and band bounds. Bands must start at `0`, be contiguous, and leave the last band unbounded (`max` empty). The page shows gaps and overlaps immediately and disables saving until the values are valid.
3. Choose **Save** to update only the config, or **Save & rescore** to queue a durable full rescore. The same-origin server proxy adds the operator key without exposing it to browser JavaScript.

The settings page reports queued/running state and polls until the worker reports how many clinics were updated. It resumes polling the active version's latest job after a page reload.

## Option B — API

Read the active config:

```bash
curl -sS http://localhost:8000/api/v1/scoring-config
```

Write a new version. This example returns **202** because it requests a rescore; use `rescore: false` for a config-only **200** response. `PUT /scoring-config` requires `X-API-Key` when `API_KEY` is set.

```bash
curl -sS -X PUT http://localhost:8000/api/v1/scoring-config \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "weights": {
      "HIRING": 25,
      "ADVERTISING": 30,
      "WEBSITE_QUALITY": 15,
      "MULTI_LOCATION": 40,
      "HIGH_TICKET": 20
    },
    "bands": [
      {"name": "COLD", "min": 0, "max": 50},
      {"name": "WARM", "min": 51, "max": 100},
      {"name": "HOT", "min": 101, "max": 150},
      {"name": "IMMEDIATE", "min": 151, "max": null}
    ],
    "rescore": true
  }'
```

`rescore: true` commits the config and job atomically, then returns immediately. Poll the returned job ID:

```bash
curl -sS http://localhost:8000/api/v1/scoring-config/rescore-jobs/<job-id>
```

The worker serializes jobs by config version. A failed full rescore is rolled back and retried up to three times; final failure details are in worker logs.

A concurrent write returns **409** `SCORING_CONFIG_CONFLICT`. Retry.

Validation failures return **422** `VALIDATION_ERROR` (missing signal keys, overlapping bands, last band not unbounded).

## Confirm

Open http://localhost:3000/clinics and check totals and bands. Clinic detail shows the per-signal breakdown that must sum to the total.
