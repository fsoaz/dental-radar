import time

from app.application.dto.enrichment_dto import ClinicAIInput, LLMCompletion
from app.application.ports.llm_provider import LLMProvider
from app.infrastructure.ai.providers.base_provider import (
    ClaudeProvider,
    GeminiProvider,
    GPTProvider,
    TransientLLMError,
)
from app.infrastructure.config.settings import Settings, settings


def create_llm_provider(
    provider_name: str | None = None,
    *,
    app_settings: Settings | None = None,
) -> LLMProvider:
    cfg = app_settings or settings
    name = (provider_name or cfg.ai_provider).lower().strip()

    common = {
        "max_site_text_chars": cfg.ai_max_site_text_chars,
        "timeout_seconds": cfg.ai_timeout_seconds,
    }

    if name == "gpt":
        return GPTProvider(
            api_key=cfg.openai_api_key,
            model=cfg.openai_model,
            **common,
        )
    if name == "claude":
        return ClaudeProvider(
            api_key=cfg.anthropic_api_key,
            model=cfg.anthropic_model,
            **common,
        )
    if name == "gemini":
        return GeminiProvider(
            api_key=cfg.gemini_api_key,
            model=cfg.gemini_model,
            **common,
        )

    raise ValueError(f"Unsupported AI provider: {name}")


def analyze_clinic_with_retries(
    provider: LLMProvider,
    payload: ClinicAIInput,
    *,
    max_retries: int = 3,
) -> LLMCompletion:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return provider.analyze_clinic(payload)
        except TransientLLMError as exc:
            last_error = exc
            if attempt == max_retries - 1:
                break
            time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def analyze_clinic_resilient(
    payload: ClinicAIInput,
    *,
    app_settings: Settings | None = None,
) -> LLMCompletion:
    cfg = app_settings or settings
    primary = create_llm_provider(cfg.ai_provider, app_settings=cfg)

    try:
        return analyze_clinic_with_retries(
            primary,
            payload,
            max_retries=cfg.ai_retry_max,
        )
    except Exception as primary_error:
        fallback_name = (cfg.ai_fallback_provider or "").strip().lower()
        if not fallback_name or fallback_name == primary.provider_name:
            raise primary_error

        fallback = create_llm_provider(fallback_name, app_settings=cfg)
        return analyze_clinic_with_retries(
            fallback,
            payload,
            max_retries=cfg.ai_retry_max,
        )
