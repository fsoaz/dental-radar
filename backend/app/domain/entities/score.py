from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_objects.priority import PriorityLevel
from app.domain.value_objects.score_breakdown import ScoreBreakdown


@dataclass
class Score:
    id: UUID
    clinic_id: UUID
    total: int
    breakdown: ScoreBreakdown
    priority: PriorityLevel
    config_version: int
    computed_at: datetime
