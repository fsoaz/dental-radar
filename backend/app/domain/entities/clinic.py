from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class Clinic:
    id: UUID
    place_id: str
    name: str
    phone: str | None = None
    website: str | None = None
    google_rating: float | None = None
    google_review_count: int = 0
    locations_count: int = 1
    social_urls: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
