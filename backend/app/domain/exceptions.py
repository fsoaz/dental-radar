class ClinicNotFoundError(Exception):
    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id
        super().__init__(f"Clinic {clinic_id} not found")


class EnrichmentFailedError(Exception):
    def __init__(self, clinic_id: str, message: str) -> None:
        self.clinic_id = clinic_id
        self.detail = message
        super().__init__(f"Enrichment failed for clinic {clinic_id}: {message}")


class ScoringConfigConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("Scoring config was updated concurrently, please retry")
