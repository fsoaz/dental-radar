from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.enrichment import Enrichment
from app.infrastructure.db.models import EnrichmentModel


class SqlAlchemyEnrichmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_clinic(self, clinic_id: UUID) -> Enrichment | None:
        model = self._session.execute(
            select(EnrichmentModel).where(EnrichmentModel.clinic_id == clinic_id)
        ).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def upsert(self, enrichment: Enrichment) -> Enrichment:
        existing = self._session.execute(
            select(EnrichmentModel).where(EnrichmentModel.clinic_id == enrichment.clinic_id)
        ).scalar_one_or_none()

        if existing is None:
            model = EnrichmentModel(
                id=enrichment.id,
                clinic_id=enrichment.clinic_id,
                growth_probability=enrichment.growth_probability,
                technology_maturity=enrichment.technology_maturity,
                marketing_sophistication=enrichment.marketing_sophistication,
                expansion_probability=enrichment.expansion_probability,
                explanation=enrichment.explanation,
                provider=enrichment.provider,
                model=enrichment.model,
                prompt_version=enrichment.prompt_version,
                input_fingerprint=enrichment.input_fingerprint,
            )
            self._session.add(model)
        else:
            enrichment.id = existing.id
            existing.growth_probability = enrichment.growth_probability
            existing.technology_maturity = enrichment.technology_maturity
            existing.marketing_sophistication = enrichment.marketing_sophistication
            existing.expansion_probability = enrichment.expansion_probability
            existing.explanation = enrichment.explanation
            existing.provider = enrichment.provider
            existing.model = enrichment.model
            existing.prompt_version = enrichment.prompt_version
            existing.input_fingerprint = enrichment.input_fingerprint

        self._session.commit()
        persisted = self.get_by_clinic(enrichment.clinic_id)
        assert persisted is not None
        return persisted

    @staticmethod
    def _to_entity(model: EnrichmentModel) -> Enrichment:
        return Enrichment(
            id=model.id,
            clinic_id=model.clinic_id,
            growth_probability=model.growth_probability or 0,
            technology_maturity=model.technology_maturity or 0,
            marketing_sophistication=model.marketing_sophistication or 0,
            expansion_probability=model.expansion_probability or 0,
            explanation=model.explanation or "",
            provider=model.provider or "",
            model=model.model or "",
            prompt_version=model.prompt_version or "",
            input_fingerprint=model.input_fingerprint or "",
            created_at=model.created_at,
        )
