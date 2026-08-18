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


class ClinicSourceError(Exception):
    """Discovery upstream failed or is misconfigured."""

    def __init__(self, message: str, *, code: str = "DISCOVERY_UNAVAILABLE") -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class UnauthorizedError(Exception):
    def __init__(self, message: str = "Invalid or missing API key") -> None:
        self.message = message
        super().__init__(message)


class ApiKeyNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "API_KEY is not configured. "
            "Set API_KEY, or ALLOW_UNAUTHENTICATED=true for local/test only."
        )


class InvalidQueryError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class RescoreJobNotFoundError(Exception):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Rescore job {job_id} not found")
