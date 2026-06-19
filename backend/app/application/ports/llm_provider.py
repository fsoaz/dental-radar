from typing import Protocol

from app.application.dto.enrichment_dto import ClinicAIInput, LLMCompletion


class LLMProvider(Protocol):
    @property
    def provider_name(self) -> str:
        """Provider identifier persisted on enrichment rows."""

    @property
    def model_name(self) -> str:
        """Model identifier persisted on enrichment rows."""

    def analyze_clinic(self, payload: ClinicAIInput) -> LLMCompletion:
        """Analyze clinic data and return structured enrichment scores."""
