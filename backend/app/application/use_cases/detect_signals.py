from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.ports.website_crawler import WebsiteCrawler
from app.domain.entities.signal import Signal
from app.domain.exceptions import ClinicNotFoundError
from app.domain.repositories.clinic_repo import ClinicRepository
from app.domain.repositories.scoring_config_repo import ScoringConfigRepository
from app.domain.repositories.signal_repo import SignalRepository
from app.domain.services.signal_detection_service import SignalDetectionService
from app.infrastructure.crawler.website_crawler import WebsiteFetchError


@dataclass
class DetectSignalsResult:
    detected: int
    signals: list[Signal]
    skipped: bool = False
    skip_reason: str | None = None


class DetectSignals:
    def __init__(
        self,
        clinic_repo: ClinicRepository,
        signal_repo: SignalRepository,
        scoring_config_repo: ScoringConfigRepository,
        crawler: WebsiteCrawler,
        detection_service: SignalDetectionService | None = None,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._signal_repo = signal_repo
        self._scoring_config_repo = scoring_config_repo
        self._crawler = crawler
        self._detection_service = detection_service or SignalDetectionService()

    def execute(self, clinic_id: UUID) -> DetectSignalsResult:
        detail = self._clinic_repo.get_detail(clinic_id)
        if detail is None:
            raise ClinicNotFoundError(str(clinic_id))

        if not detail.clinic.website:
            persisted = self._signal_repo.replace_for_clinic(clinic_id, [])
            return DetectSignalsResult(
                detected=0,
                signals=persisted,
                skipped=True,
                skip_reason="Clinic has no website",
            )

        try:
            evidence = self._crawler.fetch(detail.clinic.website)
        except WebsiteFetchError as exc:
            persisted = self._signal_repo.replace_for_clinic(clinic_id, [])
            return DetectSignalsResult(
                detected=0,
                signals=persisted,
                skipped=True,
                skip_reason=str(exc),
            )

        weights = self._scoring_config_repo.get_active_weights()
        detected = self._detection_service.detect(evidence)

        locations_count = detail.clinic.locations_count
        now = datetime.now(UTC)
        signals: list[Signal] = []
        for item in detected:
            if item.locations_count is not None:
                locations_count = item.locations_count

            signals.append(
                Signal(
                    id=uuid4(),
                    clinic_id=clinic_id,
                    type=item.signal_type,
                    applied_weight=weights.get(item.signal_type.value, 0),
                    evidence=item.evidence,
                    confidence=item.confidence,
                    detected_at=now,
                )
            )

        persisted = self._signal_repo.replace_for_clinic(clinic_id, signals)
        if locations_count != detail.clinic.locations_count:
            self._clinic_repo.update_locations_count(clinic_id, locations_count)

        return DetectSignalsResult(detected=len(persisted), signals=persisted)


class ListClinicSignals:
    def __init__(
        self,
        clinic_repo: ClinicRepository,
        signal_repo: SignalRepository,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._signal_repo = signal_repo

    def execute(self, clinic_id: UUID) -> list[Signal]:
        detail = self._clinic_repo.get_detail(clinic_id)
        if detail is None:
            raise ClinicNotFoundError(str(clinic_id))
        return self._signal_repo.list_by_clinic(clinic_id)
