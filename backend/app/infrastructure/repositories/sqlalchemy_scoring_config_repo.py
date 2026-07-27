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


def _bands_equal(left: list[ScoreBand], right: list[dict]) -> bool:
    if len(left) != len(right):
        return False
    for band, raw in zip(left, right, strict=True):
        if band.name != raw["name"] or band.min != raw["min"] or band.max != raw.get("max"):
            return False
    return True


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
        commit: bool = True,
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

        current_config = _model_to_config(current)
        if current_config.weights == weights and _bands_equal(current_config.bands, bands):
            # No-op: avoid version inflation when payload is unchanged.
            return current_config

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
            if commit:
                self._session.commit()
            else:
                self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ScoringConfigConflictError from exc
        if commit:
            self._session.refresh(new_config)
        return _model_to_config(new_config)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
