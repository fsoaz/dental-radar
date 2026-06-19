from typing import Protocol

from app.application.dto.clinic_dto import ClinicData


class ClinicSource(Protocol):
    def search(self, query: str) -> list[ClinicData]:
        """Fetch clinics matching a free-text region query."""
