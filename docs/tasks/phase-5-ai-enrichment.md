# Phase 5 — AI Enrichment (Technical Tasks)

Stories: US-E1, US-E2. Sprint S5. Goal: LLM read per clinic, provider-swappable. Default GPT.

## Tasks
- [x] `LLMProvider` port (`application/ports/llm_provider.py`): `analyze_clinic(payload) -> EnrichmentResult`.
- [x] `ClinicAIInput` DTO (name, site_text truncated, services, signals, rating, reviews, locations_count) + `EnrichmentResult` schema (4 ints 0–100 + explanation).
- [x] Prompt `infrastructure/ai/prompts/clinic_enrichment_v1.txt` (versioned).
- [x] Providers: `gpt_provider.py` (**default**), `claude_provider.py`, `gemini_provider.py` — structured/JSON output, validate + clamp + truncate per [ai_agent_rules.md](../standards/ai_agent_rules.md).
- [x] `factory.py` selecting provider from `AI_PROVIDER`; retries + optional fallback.
- [x] `EnrichmentRepository` + repo (1 row/clinic); persist provider, model, prompt_version.
- [x] Use case `EnrichClinic.execute(clinic_id, force=False)` (skip unless changed/forced).
- [x] `POST /clinics/{id}/enrich`; CLI `enrich [--all]`.
- [x] Detail + list endpoints expose `growth_probability` (list) and full breakdown (detail).
- [x] Tests: fake provider returns canned result; factory selects by env; schema validation/clamp; repair-retry path.

## Acceptance
- Enrichment returns 4 scores + explanation, persisted with provider/model/prompt_version; `AI_PROVIDER` swaps provider, identical output schema, no code change.
