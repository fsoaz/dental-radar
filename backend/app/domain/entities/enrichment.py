from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Enrichment:
    id: UUID
    clinic_id: UUID
    growth_probability: int
    technology_maturity: int
    marketing_sophistication: int
    expansion_probability: int
    explanation: str
    provider: str
    model: str
    prompt_version: str
    input_fingerprint: str
    created_at: datetime | None = None
