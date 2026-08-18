# Glossary

Terms used in the dashboard, API, and CLI. Product intent: [product.md](../explanation/product.md).

## Clinic

A dental practice ingested from Google Places. Deduped by `place_id` (Google's stable place identifier). Re-running discovery updates the same row instead of inserting a duplicate.

## Signal

Evidence that a clinic may be in a buying motion. One row per type per clinic. Types:

| Type | What the crawler looks for |
|------|----------------------------|
| `HIRING` | Jobs / careers copy (implantologist, orthodontist, receptionist, sales coordinator) |
| `ADVERTISING` | Meta Pixel, Google Ads / gtag, conversion tags |
| `WEBSITE_QUALITY` | Responsive meta, lead forms, online scheduling |
| `MULTI_LOCATION` | Multiple branches / addresses |
| `HIGH_TICKET` | Implants, Invisalign, aligners, cosmetic, veneers, oral rehab |

Each signal stores `applied_weight`, `evidence`, `confidence`, and `detected_at`.

## Score

Sum of `applied_weight` for detected signals (plus optional AI contribution in the product description; MVP total is the signal sum). Stored with a `breakdown` map and `config_version`.

## Priority band

Label derived from total score using the active `scoring_config` bands. Defaults:

| Band | Score |
|------|-------|
| `COLD` | 0–50 |
| `WARM` | 51–100 |
| `HOT` | 101–150 |
| `IMMEDIATE` | 151+ |

## Scoring config

Versioned row of weights + bands. One active version. `PUT /scoring-config` writes a new version. Operators edit it at `/settings/scoring`. See [tune scoring](../how-to/tune-scoring.md).

## Enrichment

LLM read of the clinic site + profile. Four integers 0–100 plus a short explanation:

- `growth_probability`
- `technology_maturity`
- `marketing_sophistication`
- `expansion_probability`

Persisted with `provider`, `model`, and `prompt_version` (currently `clinic_enrichment_v1`). Rules: [ai_agent_rules.md](../standards/ai_agent_rules.md).

## Operator API key

Shared secret in env `API_KEY`. Direct API callers send it as `X-API-Key` on mutating and billed routes; the dashboard's same-origin BFF injects it server-side. It is not end-user login. Per-user authentication is post-MVP.

## Place ID

Google Places `place_id`. Unique on `clinic`. The upsert key for discovery.
