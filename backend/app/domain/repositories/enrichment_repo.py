from typing import Protocol
from uuid import UUID

from app.domain.entities.enrichment import Enrichment


class EnrichmentRepository(Protocol):
    def get_by_clinic(self, clinic_id: UUID) -> Enrichment | None:
        """Return persisted enrichment for a clinic, if any."""

    def upsert(self, enrichment: Enrichment) -> Enrichment:
        """Insert or replace enrichment for a clinic."""
