from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from app.domain.entities.scoring_config import ScoreBand, ScoringConfig
from app.domain.exceptions import ScoringConfigConflictError
from app.domain.repositories.scoring_config_repo import ScoringConfigRepository
from app.infrastructure.db.models import ScoringConfigModel


def _model_to_config(model: ScoringConfigModel) -> ScoringConfig:
    bands = [
        ScoreBand(name=band["name"], min=band["min"], max=band.get("max")) for band in model.bands
    ]
    return ScoringConfig(
        version=model.version,
        active=model.active,
        weights={key: int(value) for key, value in model.weights.items()},
        bands=bands,
    )


class SqlAlchemyScoringConfigRepository(ScoringConfigRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active_weights(self) -> dict[str, int]:
        return self.get_active_config().weights

    def get_active_config(self) -> ScoringConfig:
        config = self._session.execute(
            select(ScoringConfigModel).where(ScoringConfigModel.active.is_(True))
        ).scalar_one()
        return _model_to_config(config)

    def update_active_config(
        self,
        *,
        weights: dict[str, int],
        bands: list[dict],
    ) -> ScoringConfig:
        # Lock the active row for the duration of this transaction so a concurrent
        # PUT blocks here instead of racing to compute the same next_version and
        # hitting a primary-key collision on insert.
        try:
            current = self._session.execute(
                select(ScoringConfigModel)
                .where(ScoringConfigModel.active.is_(True))
                .with_for_update()
            ).scalar_one()
        except NoResultFound as exc:
            raise ScoringConfigConflictError from exc
        current.active = False

        next_version = current.version + 1
        new_config = ScoringConfigModel(
            version=next_version,
            active=True,
            weights=weights,
            bands=bands,
        )
        self._session.add(new_config)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise ScoringConfigConflictError from exc
        self._session.refresh(new_config)
        return _model_to_config(new_config)
