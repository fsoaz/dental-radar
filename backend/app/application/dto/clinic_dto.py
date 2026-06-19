from dataclasses import dataclass

from app.domain.value_objects.address import Address


@dataclass(frozen=True)
class ClinicData:
    place_id: str
    name: str
    address: Address
    phone: str | None = None
    website: str | None = None
    google_rating: float | None = None
    google_review_count: int = 0
    social_urls: list[str] | None = None
