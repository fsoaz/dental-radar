import time
from collections.abc import Callable

from app.application.dto.enrichment_dto import ClinicAIInput, LLMCompletion
from app.application.ports.llm_provider import LLMProvider
from app.infrastructure.ai.factory import create_llm_provider
from app.infrastructure.ai.providers.base_provider import TransientLLMError
from app.infrastructure.config.settings import Settings, settings

ProviderFactory = Callable[[str, Settings], LLMProvider]


def _create_provider(name: str, app_settings: Settings) -> LLMProvider:
    return create_llm_provider(name, app_settings=app_settings)


class ResilientLLMProvider:
    """Infrastructure adapter that applies retries and optional provider fallback."""

    def __init__(
        self,
        *,
        app_settings: Settings | None = None,
        provider_factory: ProviderFactory = _create_provider,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = app_settings or settings
        if self._settings.ai_retry_max < 1:
            raise ValueError("ai_retry_max must be >= 1")
        self._sleep = sleep
        self._provider_factory = provider_factory
        self._primary_name = self._settings.ai_provider.lower().strip()
        self._primary: LLMProvider | None = None

        fallback_name = (self._settings.ai_fallback_provider or "").strip().lower()
        self._fallback_name = (
            fallback_name if fallback_name and fallback_name != self._primary_name else None
        )
        self._fallback: LLMProvider | None = None

    @property
    def provider_name(self) -> str:
        return self._primary.provider_name if self._primary is not None else self._primary_name

    @property
    def model_name(self) -> str:
        if self._primary is not None:
            return self._primary.model_name
        return {
            "gpt": self._settings.openai_model,
            "claude": self._settings.anthropic_model,
            "gemini": self._settings.gemini_model,
        }.get(self._primary_name, "")

    def analyze_clinic(self, payload: ClinicAIInput) -> LLMCompletion:
        primary = self._get_primary()
        try:
            return self._analyze_with_retries(primary, payload)
        except Exception:
            if self._fallback_name is None:
                raise
            if self._fallback is None:
                self._fallback = self._provider_factory(self._fallback_name, self._settings)
            return self._analyze_with_retries(self._fallback, payload)

    def _get_primary(self) -> LLMProvider:
        if self._primary is None:
            self._primary = self._provider_factory(self._primary_name, self._settings)
        return self._primary

    def _analyze_with_retries(
        self,
        provider: LLMProvider,
        payload: ClinicAIInput,
    ) -> LLMCompletion:
        last_error: TransientLLMError | None = None
        for attempt in range(self._settings.ai_retry_max):
            try:
                return provider.analyze_clinic(payload)
            except TransientLLMError as exc:
                last_error = exc
                if attempt == self._settings.ai_retry_max - 1:
                    break
                self._sleep(2**attempt)
        assert last_error is not None
        raise last_error
