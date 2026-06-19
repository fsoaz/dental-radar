# AI / LLM Usage Rules

Governs the AI enrichment layer. Design in [architecture.md → AI design](../context/architecture.md#5-ai-design).

## Provider abstraction
- All LLM calls go through the `LLMProvider` interface. No direct SDK calls from use cases.
- A factory selects the impl from `AI_PROVIDER` env (`gpt` default, `claude`, `gemini`). Adding a provider = new class implementing the interface; no use-case changes.
- All providers return the identical `EnrichmentResult` schema (4 integer scores 0–100 + `explanation`).

## Default models
- **GPT (default):** a current OpenAI model via `OPENAI_API_KEY`.
- **Claude:** prefer the latest capable Claude (e.g. `claude-sonnet-4-6` for cost, `claude-opus-4-8` for quality) via `ANTHROPIC_API_KEY`.
- **Gemini:** current Gemini model via `GEMINI_API_KEY`.
- Model id is configurable per provider via env; persisted on each `Enrichment` row.

## Structured output
- Request JSON / structured output mode. Validate the response against the Pydantic `EnrichmentResult` schema before persisting. On schema-invalid output → one repair retry, then fail the enrichment for that clinic (don't write partial/garbage).
- Clamp scores to 0–100; truncate `explanation` to 280 chars.

## Prompt management
- Prompts live in `infrastructure/ai/prompts/`, versioned (`clinic_enrichment_v1.txt`).
- `prompt_version` persisted with every `Enrichment` for traceability/eval.
- Change prompt = new version file; never silently edit a shipped prompt.

## Cost & rate guardrails
- Truncate website text to a max token budget before sending (e.g. first N chars of meaningful content).
- Batch enrichment as a job, not per page-view. Cache: skip re-enriching a clinic unless its site/signals changed or a force flag is set.
- Log token usage per call; surface cost in work_log during pilot.

## Reliability
- Retry transient errors (timeout/5xx/429) with exponential backoff, max 3.
- Optional fallback: if primary provider fails after retries, fall back to a secondary provider (configurable). Record which provider actually produced the result.

## Data handling / PII
- Only send public clinic data (site text, services, ratings). No private/scraped personal data beyond what's publicly on the clinic site.
- Don't send API keys or internal scores the LLM shouldn't infer from.
- Treat LLM output as advisory; it augments, never overrides, the deterministic rule-based score.

## Evaluation
- Keep a small labeled sample of clinics; on prompt/provider change, eyeball that scores + explanations stay sensible before rollout.
