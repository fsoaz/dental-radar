from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.rescore_job import RescoreJob
from app.domain.entities.scoring_config import ScoringConfig
from app.domain.exceptions import ClinicNotFoundError, RescoreJobNotFoundError
from app.domain.repositories.clinic_repo import ClinicRepository
from app.domain.repositories.rescore_job_repo import RescoreJobRepository
from app.domain.repositories.score_repo import ScoreRepository
from app.domain.repositories.scoring_config_repo import ScoringConfigRepository
from app.domain.repositories.signal_repo import SignalRepository
from app.domain.services.scoring_service import ScoringService


@dataclass
class ComputeScoreResult:
    clinic_id: UUID
    total: int
    priority: str
    breakdown: dict[str, int]
    config_version: int


class ComputeScore:
    def __init__(
        self,
        clinic_repo: ClinicRepository,
        signal_repo: SignalRepository,
        score_repo: ScoreRepository,
        scoring_config_repo: ScoringConfigRepository,
        scoring_service: ScoringService | None = None,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._signal_repo = signal_repo
        self._score_repo = score_repo
        self._scoring_config_repo = scoring_config_repo
        self._scoring_service = scoring_service or ScoringService()

    def execute(self, clinic_id: UUID) -> ComputeScoreResult:
        detail = self._clinic_repo.get_detail(clinic_id)
        if detail is None:
            raise ClinicNotFoundError(str(clinic_id))
        config = self._scoring_config_repo.get_active_config()
        return self._score_clinic(clinic_id, config, commit=True)

    def execute_existing(
        self,
        clinic_id: UUID,
        config: ScoringConfig,
        *,
        commit: bool = True,
    ) -> ComputeScoreResult:
        """Score a clinic known to exist (used by batch rescore)."""
        return self._score_clinic(clinic_id, config, commit=commit)

    def _score_clinic(
        self,
        clinic_id: UUID,
        config: ScoringConfig,
        *,
        commit: bool,
    ) -> ComputeScoreResult:
        signals = self._signal_repo.list_by_clinic(clinic_id)
        computed = self._scoring_service.compute(signals, config)

        existing = self._score_repo.get_by_clinic(clinic_id)
        score = self._scoring_service.to_score(
            clinic_id,
            computed,
            config,
            score_id=existing.id if existing else uuid4(),
            computed_at=datetime.now(UTC),
        )
        self._score_repo.upsert(score, commit=commit)

        return ComputeScoreResult(
            clinic_id=clinic_id,
            total=score.total,
            priority=score.priority.value,
            breakdown=score.breakdown.to_dict(),
            config_version=score.config_version,
        )


class RescoreAll:
    def __init__(
        self,
        clinic_repo: ClinicRepository,
        compute_score: ComputeScore,
    ) -> None:
        self._clinic_repo = clinic_repo
        self._compute_score = compute_score

    def execute(
        self,
        *,
        commit_each: bool = False,
        config: ScoringConfig | None = None,
    ) -> list[ComputeScoreResult]:
        """Rescore every clinic.

        When ``commit_each`` is False (default for config updates), scores are
        flushed in one transaction and committed by the caller — avoiding N
        round-trips and partial multi-version state on failure.
        """
        config = config or self._compute_score._scoring_config_repo.get_active_config()
        results: list[ComputeScoreResult] = []
        for clinic_id in self._clinic_repo.list_all_ids():
            results.append(
                self._compute_score.execute_existing(
                    clinic_id,
                    config,
                    commit=commit_each,
                )
            )
        return results


class GetScoringConfig:
    def __init__(
        self,
        scoring_config_repo: ScoringConfigRepository,
        rescore_job_repo: RescoreJobRepository | None = None,
    ) -> None:
        self._scoring_config_repo = scoring_config_repo
        self._rescore_job_repo = rescore_job_repo

    def execute(self) -> tuple[ScoringConfig, RescoreJob | None]:
        config = self._scoring_config_repo.get_active_config()
        job = (
            self._rescore_job_repo.latest_for_config(config.version)
            if self._rescore_job_repo is not None
            else None
        )
        return config, job


@dataclass
class UpdateScoringConfigRequest:
    weights: dict[str, int]
    bands: list[dict]
    rescore: bool = False


@dataclass
class UpdateScoringConfigResult:
    config: ScoringConfig
    rescore_job: RescoreJob | None = None


class UpdateScoringConfig:
    def __init__(
        self,
        scoring_config_repo: ScoringConfigRepository,
        rescore_job_repo: RescoreJobRepository | None = None,
    ) -> None:
        self._scoring_config_repo = scoring_config_repo
        self._rescore_job_repo = rescore_job_repo

    def execute(self, request: UpdateScoringConfigRequest) -> UpdateScoringConfigResult:
        defer_commit = bool(request.rescore and self._rescore_job_repo is not None)
        config = self._scoring_config_repo.update_active_config(
            weights=request.weights,
            bands=request.bands,
            commit=not defer_commit,
        )
        job = None
        if defer_commit and self._rescore_job_repo is not None:
            try:
                job = self._rescore_job_repo.enqueue(config.version)
                self._scoring_config_repo.commit()
            except Exception:
                self._scoring_config_repo.rollback()
                raise
        return UpdateScoringConfigResult(config=config, rescore_job=job)


class GetRescoreJob:
    def __init__(self, rescore_job_repo: RescoreJobRepository) -> None:
        self._rescore_job_repo = rescore_job_repo

    def execute(self, job_id: UUID) -> RescoreJob:
        job = self._rescore_job_repo.get(job_id)
        if job is None:
            raise RescoreJobNotFoundError(str(job_id))
        return job
