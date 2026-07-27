from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.scoring_config import ScoringConfig
from app.domain.exceptions import ClinicNotFoundError
from app.domain.repositories.clinic_repo import ClinicRepository
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

    def execute(self, *, commit_each: bool = False) -> list[ComputeScoreResult]:
        """Rescore every clinic.

        When ``commit_each`` is False (default for config updates), scores are
        flushed in one transaction and committed by the caller — avoiding N
        round-trips and partial multi-version state on failure.
        """
        config = self._compute_score._scoring_config_repo.get_active_config()
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
    def __init__(self, scoring_config_repo: ScoringConfigRepository) -> None:
        self._scoring_config_repo = scoring_config_repo

    def execute(self) -> ScoringConfig:
        return self._scoring_config_repo.get_active_config()


@dataclass
class UpdateScoringConfigRequest:
    weights: dict[str, int]
    bands: list[dict]
    rescore: bool = False


@dataclass
class UpdateScoringConfigResult:
    config: ScoringConfig
    rescored: int = 0


class UpdateScoringConfig:
    def __init__(
        self,
        scoring_config_repo: ScoringConfigRepository,
        rescore_all: RescoreAll | None = None,
    ) -> None:
        self._scoring_config_repo = scoring_config_repo
        self._rescore_all = rescore_all

    def execute(self, request: UpdateScoringConfigRequest) -> UpdateScoringConfigResult:
        # Defer commit when rescoring so a mid-loop failure rolls back the new
        # config together with any partial score writes.
        defer_commit = bool(request.rescore and self._rescore_all is not None)
        config = self._scoring_config_repo.update_active_config(
            weights=request.weights,
            bands=request.bands,
            commit=not defer_commit,
        )
        rescored = 0
        if defer_commit and self._rescore_all is not None:
            try:
                rescored = len(self._rescore_all.execute(commit_each=False))
                self._scoring_config_repo.commit()
            except Exception:
                self._scoring_config_repo.rollback()
                raise
        return UpdateScoringConfigResult(config=config, rescored=rescored)
