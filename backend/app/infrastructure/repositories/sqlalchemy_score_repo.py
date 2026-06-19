from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.score import Score
from app.domain.value_objects.priority import PriorityLevel
from app.domain.value_objects.score_breakdown import ScoreBreakdown
from app.infrastructure.db.models import ScoreModel


class SqlAlchemyScoreRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, score: Score) -> Score:
        existing = self._session.execute(
            select(ScoreModel).where(ScoreModel.clinic_id == score.clinic_id)
        ).scalar_one_or_none()

        if existing is None:
            model = ScoreModel(
                id=score.id,
                clinic_id=score.clinic_id,
                total=score.total,
                breakdown=score.breakdown.to_dict(),
                priority=score.priority.value,
                config_version=score.config_version,
                computed_at=score.computed_at,
            )
            self._session.add(model)
        else:
            score.id = existing.id
            existing.total = score.total
            existing.breakdown = score.breakdown.to_dict()
            existing.priority = score.priority.value
            existing.config_version = score.config_version
            existing.computed_at = score.computed_at

        self._session.commit()
        persisted = self.get_by_clinic(score.clinic_id)
        assert persisted is not None
        return persisted

    def get_by_clinic(self, clinic_id: UUID) -> Score | None:
        model = self._session.execute(
            select(ScoreModel).where(ScoreModel.clinic_id == clinic_id)
        ).scalar_one_or_none()
        if model is None:
            return None
        return Score(
            id=model.id,
            clinic_id=model.clinic_id,
            total=model.total,
            breakdown=ScoreBreakdown(points_by_type=dict(model.breakdown)),
            priority=PriorityLevel(model.priority),
            config_version=model.config_version or 0,
            computed_at=model.computed_at,
        )
