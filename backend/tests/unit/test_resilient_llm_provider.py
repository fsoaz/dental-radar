from collections.abc import Iterable

import pytest

from app.application.dto.enrichment_dto import (
    ClinicAIInput,
    EnrichmentResult,
    LLMCompletion,
)
from app.infrastructure.ai.providers.base_provider import (
    ConfigurationError,
    TransientLLMError,
)
from app.infrastructure.ai.resilient_provider import ResilientLLMProvider
from app.infrastructure.config.settings import Settings

PAYLOAD = ClinicAIInput(
    name="Smile Dental",
    site_text="Modern clinic",
    signals=[],
    rating=4.5,
    reviews=100,
    locations_count=1,
)


def _completion(provider: str, model: str) -> LLMCompletion:
    return LLMCompletion(
        provider=provider,
        model=model,
        prompt_version="clinic_enrichment_v1",
        result=EnrichmentResult(
            growth_probability=70,
            technology_maturity=60,
            marketing_sophistication=50,
            expansion_probability=40,
            explanation="Test result",
        ),
    )


class _ScriptedProvider:
    def __init__(self, name: str, model: str, outcomes: Iterable[object]) -> None:
        self.provider_name = name
        self.model_name = model
        self._outcomes = iter(outcomes)
        self.calls = 0

    def analyze_clinic(self, payload: ClinicAIInput) -> LLMCompletion:
        assert payload is PAYLOAD
        self.calls += 1
        outcome = next(self._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, LLMCompletion)
        return outcome


def _adapter(
    providers: dict[str, _ScriptedProvider],
    *,
    fallback: str = "",
    retries: int = 3,
    sleeps: list[float] | None = None,
) -> ResilientLLMProvider:
    cfg = Settings(
        ai_provider="gpt",
        ai_fallback_provider=fallback,
        ai_retry_max=retries,
    )
    return ResilientLLMProvider(
        app_settings=cfg,
        provider_factory=lambda name, _settings: providers[name],
        sleep=(sleeps.append if sleeps is not None else lambda _seconds: None),
    )


def test_resilient_provider_returns_primary_success() -> None:
    primary = _ScriptedProvider("gpt", "primary-model", [_completion("gpt", "primary-model")])

    result = _adapter({"gpt": primary}).analyze_clinic(PAYLOAD)

    assert primary.calls == 1
    assert (result.provider, result.model) == ("gpt", "primary-model")


def test_resilient_provider_retries_transient_failures_with_exponential_delays() -> None:
    sleeps: list[float] = []
    primary = _ScriptedProvider(
        "gpt",
        "primary-model",
        [
            TransientLLMError("first"),
            TransientLLMError("second"),
            _completion("gpt", "primary-model"),
        ],
    )

    result = _adapter({"gpt": primary}, sleeps=sleeps).analyze_clinic(PAYLOAD)

    assert primary.calls == 3
    assert sleeps == [1, 2]
    assert result.provider == "gpt"


def test_resilient_provider_raises_after_retry_exhaustion() -> None:
    primary = _ScriptedProvider(
        "gpt",
        "primary-model",
        [TransientLLMError("one"), TransientLLMError("two")],
    )

    with pytest.raises(TransientLLMError, match="two"):
        _adapter({"gpt": primary}, retries=2).analyze_clinic(PAYLOAD)

    assert primary.calls == 2


def test_resilient_provider_uses_fallback_and_preserves_actual_metadata() -> None:
    primary = _ScriptedProvider("gpt", "primary-model", [TransientLLMError("down")])
    fallback = _ScriptedProvider(
        "claude",
        "fallback-model",
        [_completion("claude", "fallback-model")],
    )

    result = _adapter(
        {"gpt": primary, "claude": fallback},
        fallback="claude",
        retries=1,
    ).analyze_clinic(PAYLOAD)

    assert (result.provider, result.model) == ("claude", "fallback-model")
    assert fallback.calls == 1


def test_resilient_provider_does_not_retry_permanent_error_before_fallback() -> None:
    primary = _ScriptedProvider("gpt", "primary-model", [ConfigurationError("missing key")])
    fallback = _ScriptedProvider(
        "claude",
        "fallback-model",
        [_completion("claude", "fallback-model")],
    )

    result = _adapter(
        {"gpt": primary, "claude": fallback},
        fallback="claude",
    ).analyze_clinic(PAYLOAD)

    assert primary.calls == 1
    assert result.provider == "claude"


def test_resilient_provider_reraises_when_no_fallback_is_configured() -> None:
    primary = _ScriptedProvider("gpt", "primary-model", [ConfigurationError("missing key")])

    with pytest.raises(ConfigurationError, match="missing key"):
        _adapter({"gpt": primary}).analyze_clinic(PAYLOAD)


def test_resilient_provider_defers_primary_creation_until_analysis() -> None:
    created: list[str] = []

    def invalid_provider(name: str, _settings: Settings):
        created.append(name)
        raise ValueError(f"Unsupported AI provider: {name}")

    provider = ResilientLLMProvider(
        app_settings=Settings(ai_provider="bogus"),
        provider_factory=invalid_provider,
        sleep=lambda _seconds: None,
    )

    assert created == []
    assert provider.provider_name == "bogus"

    with pytest.raises(ValueError, match="Unsupported AI provider: bogus"):
        provider.analyze_clinic(PAYLOAD)

    assert created == ["bogus"]
