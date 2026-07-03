import pytest
from pydantic import ValidationError

from app.infrastructure.ai.factory import create_llm_provider
from app.infrastructure.ai.providers.base_provider import (
    ClaudeProvider,
    GeminiProvider,
    GPTProvider,
)
from app.infrastructure.config.settings import DEFAULT_OPENAI_BASE_URL, Settings


@pytest.mark.parametrize(
    ("provider_name", "expected_cls"),
    [
        ("gpt", GPTProvider),
        ("claude", ClaudeProvider),
        ("gemini", GeminiProvider),
    ],
)
def test_factory_selects_provider_by_env(provider_name, expected_cls):
    cfg = Settings(ai_provider=provider_name)
    provider = create_llm_provider(app_settings=cfg)
    assert isinstance(provider, expected_cls)
    assert provider.provider_name == provider_name


def test_factory_passes_openai_base_url():
    cfg = Settings(ai_provider="gpt", openai_base_url="https://openrouter.ai/api/v1/")
    provider = create_llm_provider(app_settings=cfg)
    assert isinstance(provider, GPTProvider)
    assert provider._base_url == "https://openrouter.ai/api/v1"


def test_settings_blank_openai_base_url_falls_back_to_default():
    cfg = Settings(openai_base_url="   ")
    assert cfg.openai_base_url == DEFAULT_OPENAI_BASE_URL


def test_settings_accepts_case_insensitive_https_scheme():
    cfg = Settings(openai_base_url="HTTPS://openrouter.ai/api/v1/")
    assert cfg.openai_base_url == "HTTPS://openrouter.ai/api/v1"


def test_settings_rejects_non_https_openai_base_url():
    with pytest.raises(ValidationError, match="OPENAI_BASE_URL must use https://"):
        Settings(openai_base_url="http://internal-proxy/v1")


def test_factory_rejects_unknown_provider():
    cfg = Settings(ai_provider="unknown")
    with pytest.raises(ValueError, match="Unsupported AI provider"):
        create_llm_provider(app_settings=cfg)
