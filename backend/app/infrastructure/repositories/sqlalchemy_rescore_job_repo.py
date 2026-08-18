from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.rescore_job import RescoreJob
from app.infrastructure.db.models import RescoreJobModel


def _to_entity(model: RescoreJobModel) -> RescoreJob:
    return RescoreJob(
        id=model.id,
        config_version=model.config_version,
        status=model.status,
        attempts=model.attempts,
        rescored=model.rescored,
        error_message=model.error_message,
        created_at=model.created_at,
        started_at=model.started_at,
        finished_at=model.finished_at,
    )


class SqlAlchemyRescoreJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue(self, config_version: int) -> RescoreJob:
        model = RescoreJobModel(config_version=config_version, status="queued")
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def get(self, job_id: UUID) -> RescoreJob | None:
        model = self._session.get(RescoreJobModel, job_id)
        return _to_entity(model) if model is not None else None

    def latest_for_config(self, config_version: int) -> RescoreJob | None:
        model = self._session.execute(
            select(RescoreJobModel)
            .where(RescoreJobModel.config_version == config_version)
            .order_by(RescoreJobModel.created_at.desc(), RescoreJobModel.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    def recover_running(self) -> None:
        for model in self._session.execute(
            select(RescoreJobModel).where(RescoreJobModel.status == "running")
        ).scalars():
            model.status = "queued"
            model.started_at = None
        self._session.commit()

    def claim_next(self) -> RescoreJob | None:
        model = self._session.execute(
            select(RescoreJobModel)
            .where(RescoreJobModel.status == "queued", RescoreJobModel.attempts < 3)
            .order_by(RescoreJobModel.created_at, RescoreJobModel.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).scalar_one_or_none()
        if model is None:
            self._session.rollback()
            return None
        model.status = "running"
        model.attempts += 1
        model.started_at = datetime.now(UTC)
        model.finished_at = None
        model.error_message = None
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def succeed(self, job_id: UUID, rescored: int) -> None:
        model = self._session.get(RescoreJobModel, job_id)
        if model is None:
            return
        model.status = "succeeded"
        model.rescored = rescored
        model.finished_at = datetime.now(UTC)
        self._session.commit()

    def fail(self, job_id: UUID) -> None:
        model = self._session.get(RescoreJobModel, job_id)
        if model is None:
            return
        model.status = "failed" if model.attempts >= 3 else "queued"
        model.error_message = "Rescore failed. Check worker logs for details."
        model.finished_at = datetime.now(UTC) if model.status == "failed" else None
        self._session.commit()
