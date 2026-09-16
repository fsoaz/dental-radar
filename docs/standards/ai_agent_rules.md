# LLM provider rules

How enrichment calls providers, prompts, retries, and fallback. Wiring: [`resilient_provider.py`](../../backend/app/infrastructure/ai/resilient_provider.py), [`factory.py`](../../backend/app/infrastructure/ai/factory.py), [`base_provider.py`](../../backend/app/infrastructure/ai/providers/base_provider.py), [`enrichment_parser.py`](../../backend/app/infrastructure/ai/enrichment_parser.py).

Env catalog: [environment.md](../reference/environment.md). Product shape: [architecture → AI design](../explanation/architecture.md#5-ai-design).

## Provider selection

`AI_PROVIDER` is `gpt` (default), `claude`, or `gemini`. The factory returns one implementation. Output schema is the same for every provider:

```json
{
  "growth_probability": 0,
  "technology_maturity": 0,
  "marketing_sophistication": 0,
  "expansion_probability": 0,
  "explanation": "string, <= 280 chars"
}
```

Scores are integers 0–100. The parser validates, clamps, and truncates the explanation.

| Provider | Env key | Notes |
|----------|---------|-------|
| `gpt` | `OPENAI_API_KEY` | `OPENAI_BASE_URL` must be `https://` (OpenRouter and other OpenAI-compatible hosts). Keys go in the `Authorization` header, never in the URL. |
| `claude` | `ANTHROPIC_API_KEY` | `x-api-key` header. |
| `gemini` | `GEMINI_API_KEY` | `x-goog-api-key` header. |

Missing keys raise `ConfigurationError` immediately. That error is **not** retried.

The resilient adapter creates the primary provider on the first enrichment call, not at startup or dependency resolution. An unsupported `AI_PROVIDER` therefore fails inside enrichment: the API returns **502** `ENRICHMENT_FAILED`, and CLI commands still start.

## Prompt

Version `clinic_enrichment_v1`, file `backend/app/infrastructure/ai/prompts/clinic_enrichment_v1.txt`. Each stored enrichment records `prompt_version`.

Site text is truncated to `AI_MAX_SITE_TEXT_CHARS` (default 8000) before it enters the user prompt.

## Parse repair

If the first completion is not valid JSON for the schema, the provider sends one repair turn (`REPAIR_USER_SUFFIX`) with the previous raw text and asks for corrected JSON only. A second parse failure becomes a transient/enrichment failure.

## Retries

`ResilientLLMProvider` retries **transient** failures (`TransientLLMError`: timeouts, 408/429/5xx, network, empty Gemini candidates). It does not retry missing keys or other configuration errors.

- Attempts: `AI_RETRY_MAX` (default 3)
- Backoff: `2 ** attempt` seconds between tries
- Timeout per call: `AI_TIMEOUT_SECONDS` (default 60)

## Fallback

If the primary provider still fails and `AI_FALLBACK_PROVIDER` is set to a **different** name, the resilient adapter runs the same retry loop against that provider. Empty or identical fallback is ignored; the original error is raised. Completion metadata records the provider and model that actually returned the result.

The HTTP API maps a final failure to **502** `ENRICHMENT_FAILED` without leaking upstream response bodies to the client.

## Skip vs force

`EnrichClinic` skips when inputs are unchanged (`skip_reason`: `Inputs unchanged`) unless `force=true` (query param or CLI `--force`).
