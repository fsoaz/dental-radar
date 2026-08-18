from typing import Protocol
from uuid import UUID

from app.domain.entities.rescore_job import RescoreJob


class RescoreJobRepository(Protocol):
    def enqueue(self, config_version: int) -> RescoreJob: ...

    def get(self, job_id: UUID) -> RescoreJob | None: ...

    def latest_for_config(self, config_version: int) -> RescoreJob | None: ...
