from app.application.ports.llm_provider import LLMProvider
from app.infrastructure.ai.providers.base_provider import (
    ClaudeProvider,
    GeminiProvider,
    GPTProvider,
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
            base_url=cfg.openai_base_url,
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
