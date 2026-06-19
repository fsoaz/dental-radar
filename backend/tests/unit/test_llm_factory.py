import pytest

from app.infrastructure.ai.factory import create_llm_provider
from app.infrastructure.ai.providers.base_provider import (
    ClaudeProvider,
    GeminiProvider,
    GPTProvider,
)
from app.infrastructure.config.settings import Settings


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


def test_factory_rejects_unknown_provider():
    cfg = Settings(ai_provider="unknown")
    with pytest.raises(ValueError, match="Unsupported AI provider"):
        create_llm_provider(app_settings=cfg)
