from typing import Protocol
from uuid import UUID

from app.domain.entities.score import Score


class ScoreRepository(Protocol):
    def upsert(self, score: Score, *, commit: bool = True) -> Score:
        """Create or replace the score row for a clinic."""

    def get_by_clinic(self, clinic_id: UUID) -> Score | None:
        """Return the persisted score for a clinic, if any."""
