from uuid import UUID

from app.domain.exceptions import ClinicNotFoundError
from app.domain.repositories.clinic_repo import (
    ClinicDetail,
    ClinicListQuery,
    ClinicListResult,
    ClinicRepository,
)


class ListClinics:
    def __init__(self, clinic_repo: ClinicRepository) -> None:
        self._clinic_repo = clinic_repo

    def execute(self, query: ClinicListQuery) -> ClinicListResult:
        return self._clinic_repo.list_clinics(query)


class GetClinic:
    def __init__(self, clinic_repo: ClinicRepository) -> None:
        self._clinic_repo = clinic_repo

    def execute(self, clinic_id: UUID) -> ClinicDetail:
        detail = self._clinic_repo.get_detail(clinic_id)
        if detail is None:
            raise ClinicNotFoundError(str(clinic_id))
        return detail
