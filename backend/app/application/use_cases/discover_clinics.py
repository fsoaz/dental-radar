from dataclasses import dataclass
from uuid import uuid4

from app.application.dto.clinic_dto import ClinicData
from app.application.ports.clinic_source import ClinicSource
from app.domain.entities.clinic import Clinic
from app.domain.entities.location import Location
from app.domain.repositories.clinic_repo import ClinicRepository


@dataclass
class DiscoverClinicsResult:
    ingested: int
    created: int
    updated: int


class DiscoverClinics:
    def __init__(self, clinic_source: ClinicSource, clinic_repo: ClinicRepository) -> None:
        self._clinic_source = clinic_source
        self._clinic_repo = clinic_repo

    def execute(self, query: str) -> DiscoverClinicsResult:
        clinics_data = self._clinic_source.search(query)
        created = 0
        updated = 0

        for data in clinics_data:
            clinic, was_created = self._upsert_clinic(data)
            if was_created:
                created += 1
            else:
                updated += 1

        return DiscoverClinicsResult(
            ingested=len(clinics_data),
            created=created,
            updated=updated,
        )

    def _upsert_clinic(self, data: ClinicData) -> tuple[Clinic, bool]:
        clinic = Clinic(
            id=uuid4(),
            place_id=data.place_id,
            name=data.name,
            phone=data.phone,
            website=data.website,
            google_rating=data.google_rating,
            google_review_count=data.google_review_count,
            social_urls=list(data.social_urls or []),
        )
        location = Location(
            id=uuid4(),
            clinic_id=clinic.id,
            address=data.address,
            is_primary=True,
        )
        return self._clinic_repo.upsert(clinic, location)
