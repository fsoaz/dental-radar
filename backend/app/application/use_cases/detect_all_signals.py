from uuid import UUID

from app.application.use_cases.detect_signals import DetectSignals


class DetectAllSignals:
    def __init__(
        self,
        clinic_repo,
        detect_signals: DetectSignals,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._detect_signals = detect_signals

    def execute(self) -> list[tuple[UUID, int]]:
        results: list[tuple[UUID, int]] = []
        for clinic_id in self._clinic_repo.list_ids_with_website():
            result = self._detect_signals.execute(clinic_id)
            results.append((clinic_id, result.detected))
        return results
