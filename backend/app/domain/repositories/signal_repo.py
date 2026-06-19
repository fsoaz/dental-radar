from typing import Protocol
from uuid import UUID

from app.domain.entities.signal import Signal


class SignalRepository(Protocol):
    def replace_for_clinic(self, clinic_id: UUID, signals: list[Signal]) -> list[Signal]:
        """Replace all signals for a clinic with the newly detected set."""

    def list_by_clinic(self, clinic_id: UUID) -> list[Signal]:
        """Return persisted signals for a clinic."""
