import httpx
import pytest

from app.application.dto.enrichment_dto import ClinicAIInput, EnrichmentResult, SignalSummary
from app.infrastructure.ai.enrichment_parser import (
    EnrichmentParseError,
    compute_input_fingerprint,
    parse_enrichment_response,
    truncate_site_text,
)
from app.infrastructure.ai.providers.base_provider import GPTProvider, TransientLLMError
from app.infrastructure.config.settings import DEFAULT_OPENAI_BASE_URL


def test_parse_enrichment_response_clamps_scores():
    raw = """
    {
      "growth_probability": 150,
      "technology_maturity": -5,
      "marketing_sophistication": 72,
      "expansion_probability": 80,
      "explanation": "Strong market presence."
    }
    """
    result = parse_enrichment_response(raw)
    assert result.growth_probability == 100
    assert result.technology_maturity == 0
    assert result.marketing_sophistication == 72


def test_parse_enrichment_response_truncates_explanation():
    long_text = "x" * 400
    raw = (
        '{"growth_probability": 10, "technology_maturity": 10, '
        '"marketing_sophistication": 10, "expansion_probability": 10, '
        f'"explanation": "{long_text}"}}'
    )
    result = parse_enrichment_response(raw)
    assert len(result.explanation) == 280


def test_parse_enrichment_response_rejects_invalid_schema():
    with pytest.raises(EnrichmentParseError):
        parse_enrichment_response('{"growth_probability": "high"}')


def test_repair_retry_path_uses_second_response():
    provider = GPTProvider(api_key="test-key", model="gpt-test")
    responses = iter(
        [
            "not-json",
            (
                '{"growth_probability": 55, "technology_maturity": 44, '
                '"marketing_sophistication": 33, "expansion_probability": 22, '
                '"explanation": "Recovered after repair."}'
            ),
        ]
    )
    provider._complete = lambda _system, _user: next(responses)  # type: ignore[method-assign]

    payload = ClinicAIInput(
        name="Smile Dental",
        site_text="Modern dental clinic",
        signals=[SignalSummary(type="HIRING", evidence="hiring page")],
        rating=4.5,
        reviews=100,
        locations_count=1,
    )
    completion = provider.analyze_clinic(payload)
    assert completion.result.growth_probability == 55
    assert completion.result.explanation == "Recovered after repair."


def test_gpt_provider_uses_configured_base_url(monkeypatch):
    captured: dict[str, object] = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"growth_probability": 55, "technology_maturity": 44, '
                                '"marketing_sophistication": 33, "expansion_probability": 22, '
                                '"explanation": "OpenRouter response."}'
                            )
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr("app.infrastructure.ai.providers.base_provider.httpx.post", fake_post)
    provider = GPTProvider(
        api_key="test-key",
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1/",
    )

    payload = ClinicAIInput(
        name="Smile Dental",
        site_text="Modern dental clinic",
        signals=[SignalSummary(type="HIRING", evidence="hiring page")],
        rating=4.5,
        reviews=100,
        locations_count=1,
    )
    completion = provider.analyze_clinic(payload)

    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["json"]["model"] == "openai/gpt-4o-mini"
    assert completion.result.explanation == "OpenRouter response."


def test_gpt_provider_blank_base_url_falls_back_to_openai():
    provider = GPTProvider(api_key="k", model="m", base_url="   ")
    assert provider._base_url == DEFAULT_OPENAI_BASE_URL


def test_provider_raises_http_error_for_redirect_response():
    provider = GPTProvider(api_key="k", model="m")
    response = httpx.Response(
        302,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        text="Redirecting",
    )

    with pytest.raises(httpx.HTTPStatusError, match="gpt error 302"):
        provider._raise_for_status(response)


def test_provider_raises_transient_error_for_retryable_status():
    provider = GPTProvider(api_key="k", model="m")
    response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        text="Rate limited",
    )

    with pytest.raises(TransientLLMError, match="gpt transient error 429"):
        provider._raise_for_status(response)


def test_compute_input_fingerprint_changes_when_signals_change():
    base = ClinicAIInput(
        name="Smile Dental",
        site_text="site",
        signals=[SignalSummary(type="HIRING", evidence="jobs")],
        rating=4.5,
        reviews=10,
        locations_count=1,
    )
    changed = ClinicAIInput(
        name="Smile Dental",
        site_text="site",
        signals=[SignalSummary(type="ADVERTISING", evidence="ads")],
        rating=4.5,
        reviews=10,
        locations_count=1,
    )
    assert compute_input_fingerprint(base, 8000) != compute_input_fingerprint(changed, 8000)


def test_truncate_site_text_respects_limit():
    text = "word " * 1000
    truncated = truncate_site_text(text, 50)
    assert len(truncated) <= 51
    assert truncated.endswith("…")


def test_enrichment_result_accepts_clamped_values():
    result = EnrichmentResult.model_validate(
        {
            "growth_probability": 101,
            "technology_maturity": 0,
            "marketing_sophistication": 0,
            "expansion_probability": 0,
            "explanation": "clamped",
        }
    )
    assert result.growth_probability == 100
