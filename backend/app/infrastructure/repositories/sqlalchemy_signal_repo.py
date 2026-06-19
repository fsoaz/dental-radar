from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.entities.signal import Signal
from app.domain.repositories.signal_repo import SignalRepository
from app.domain.value_objects.signal_type import SignalType
from app.infrastructure.db.models import SignalModel


def signal_model_to_entity(model: SignalModel) -> Signal:
    return Signal(
        id=model.id,
        clinic_id=model.clinic_id,
        type=SignalType(model.type),
        applied_weight=model.applied_weight,
        evidence=model.evidence or "",
        confidence=float(model.confidence),
        detected_at=model.detected_at,
    )


class SqlAlchemySignalRepository(SignalRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_clinic(self, clinic_id: UUID, signals: list[Signal]) -> list[Signal]:
        self._session.execute(delete(SignalModel).where(SignalModel.clinic_id == clinic_id))

        persisted: list[Signal] = []
        now = datetime.now(UTC)
        for signal in signals:
            model = SignalModel(
                id=signal.id,
                clinic_id=clinic_id,
                type=signal.type.value,
                applied_weight=signal.applied_weight,
                evidence=signal.evidence,
                confidence=signal.confidence,
                detected_at=signal.detected_at or now,
            )
            self._session.add(model)
            persisted.append(signal_model_to_entity(model))

        self._session.commit()
        return persisted

    def list_by_clinic(self, clinic_id: UUID) -> list[Signal]:
        models = self._session.execute(
            select(SignalModel)
            .where(SignalModel.clinic_id == clinic_id)
            .order_by(SignalModel.type.asc())
        ).scalars()
        return [signal_model_to_entity(model) for model in models]
