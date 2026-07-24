from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.dto.enrichment_dto import ClinicAIInput, SignalSummary
from app.application.ports.llm_provider import LLMProvider
from app.application.ports.website_crawler import WebsiteCrawler
from app.domain.entities.enrichment import Enrichment
from app.domain.exceptions import ClinicNotFoundError, EnrichmentFailedError
from app.domain.repositories.clinic_repo import ClinicRepository
from app.domain.repositories.enrichment_repo import EnrichmentRepository
from app.infrastructure.ai.enrichment_parser import compute_input_fingerprint
from app.infrastructure.ai.factory import analyze_clinic_resilient
from app.infrastructure.config.settings import Settings, settings
from app.infrastructure.crawler.website_crawler import WebsiteFetchError


@dataclass
class EnrichClinicResult:
    clinic_id: UUID
    growth_probability: int
    technology_maturity: int
    marketing_sophistication: int
    expansion_probability: int
    explanation: str
    provider: str
    model: str
    prompt_version: str
    skipped: bool = False
    skip_reason: str | None = None


class EnrichClinic:
    def __init__(
        self,
        clinic_repo: ClinicRepository,
        enrichment_repo: EnrichmentRepository,
        crawler: WebsiteCrawler,
        llm_provider: LLMProvider | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._enrichment_repo = enrichment_repo
        self._crawler = crawler
        self._llm_provider = llm_provider
        self._settings = app_settings or settings

    def execute(self, clinic_id: UUID, *, force: bool = False) -> EnrichClinicResult:
        detail = self._clinic_repo.get_detail(clinic_id)
        if detail is None:
            raise ClinicNotFoundError(str(clinic_id))

        payload = self._build_payload(detail)
        fingerprint = compute_input_fingerprint(payload, self._settings.ai_max_site_text_chars)

        existing = self._enrichment_repo.get_by_clinic(clinic_id)
        if existing is not None and not force and existing.input_fingerprint == fingerprint:
            return self._to_result(existing, skipped=True, skip_reason="Inputs unchanged")

        try:
            if self._llm_provider is not None:
                completion = self._llm_provider.analyze_clinic(payload)
            else:
                completion = analyze_clinic_resilient(payload, app_settings=self._settings)
        except Exception as exc:
            raise EnrichmentFailedError(str(clinic_id), str(exc)) from exc

        enrichment = Enrichment(
            id=existing.id if existing else uuid4(),
            clinic_id=clinic_id,
            growth_probability=completion.result.growth_probability,
            technology_maturity=completion.result.technology_maturity,
            marketing_sophistication=completion.result.marketing_sophistication,
            expansion_probability=completion.result.expansion_probability,
            explanation=completion.result.explanation,
            provider=completion.provider,
            model=completion.model,
            prompt_version=completion.prompt_version,
            input_fingerprint=fingerprint,
            created_at=datetime.now(UTC),
        )
        persisted = self._enrichment_repo.upsert(enrichment)
        return self._to_result(persisted)

    def _build_payload(self, detail) -> ClinicAIInput:
        site_text = ""
        if detail.clinic.website:
            try:
                evidence = self._crawler.fetch(detail.clinic.website)
                site_text = evidence.text
            except WebsiteFetchError:
                site_text = ""

        signals = [
            SignalSummary(type=signal["type"], evidence=signal.get("evidence"))
            for signal in detail.signals
        ]

        return ClinicAIInput(
            name=detail.clinic.name,
            site_text=site_text,
            signals=signals,
            rating=detail.clinic.google_rating,
            reviews=detail.clinic.google_review_count,
            locations_count=detail.clinic.locations_count,
        )

    @staticmethod
    def _to_result(
        enrichment: Enrichment,
        *,
        skipped: bool = False,
        skip_reason: str | None = None,
    ) -> EnrichClinicResult:
        return EnrichClinicResult(
            clinic_id=enrichment.clinic_id,
            growth_probability=enrichment.growth_probability,
            technology_maturity=enrichment.technology_maturity,
            marketing_sophistication=enrichment.marketing_sophistication,
            expansion_probability=enrichment.expansion_probability,
            explanation=enrichment.explanation,
            provider=enrichment.provider,
            model=enrichment.model,
            prompt_version=enrichment.prompt_version,
            skipped=skipped,
            skip_reason=skip_reason,
        )


class EnrichAllClinics:
    def __init__(
        self,
        clinic_repo: ClinicRepository,
        enrich_clinic: EnrichClinic,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._enrich_clinic = enrich_clinic

    def execute(self, *, force: bool = False) -> list[EnrichClinicResult]:
        results: list[EnrichClinicResult] = []
        for clinic_id in self._clinic_repo.list_all_ids():
            results.append(self._enrich_clinic.execute(clinic_id, force=force))
        return results
