from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.score import Score
from app.domain.entities.scoring_config import ScoringConfig
from app.domain.entities.signal import Signal
from app.domain.value_objects.priority import PriorityLevel
from app.domain.value_objects.score_breakdown import ScoreBreakdown


@dataclass(frozen=True)
class ComputedScore:
    total: int
    breakdown: ScoreBreakdown
    priority: PriorityLevel


class ScoringService:
    def compute(self, signals: list[Signal], config: ScoringConfig) -> ComputedScore:
        breakdown = ScoreBreakdown.from_signals(signals, config.weights)
        breakdown.validate()
        total = breakdown.total
        priority = PriorityLevel(config.priority_for_total(total))
        return ComputedScore(total=total, breakdown=breakdown, priority=priority)

    def to_score(
        self,
        clinic_id: UUID,
        computed: ComputedScore,
        config: ScoringConfig,
        *,
        score_id: UUID | None = None,
        computed_at: datetime | None = None,
    ) -> Score:
        return Score(
            id=score_id or uuid4(),
            clinic_id=clinic_id,
            total=computed.total,
            breakdown=computed.breakdown,
            priority=computed.priority,
            config_version=config.version,
            computed_at=computed_at or datetime.now(UTC),
        )
