from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_objects.signal_type import SignalType


@dataclass
class Signal:
    id: UUID
    clinic_id: UUID
    type: SignalType
    applied_weight: int
    evidence: str
    confidence: float
    detected_at: datetime
