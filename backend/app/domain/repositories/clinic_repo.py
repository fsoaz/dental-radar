from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.entities.clinic import Clinic
from app.domain.entities.location import Location


@dataclass
class ClinicListItem:
    clinic: Clinic
    city: str | None
    state: str | None
    score: int | None = None
    priority: str | None = None
    growth_probability: int | None = None


@dataclass
class ClinicDetail:
    clinic: Clinic
    primary_location: Location | None
    signals: list
    score: dict | None
    enrichment: dict | None


@dataclass
class ClinicListResult:
    items: list[ClinicListItem]
    total: int


@dataclass
class ClinicListQuery:
    q: str | None = None
    state: str | None = None
    priority: str | None = None
    min_score: int | None = None
    max_score: int | None = None
    has_website: bool | None = None
    signal_type: str | None = None
    sort: str = "-score"
    page: int = 1
    page_size: int = 20


class ClinicRepository(Protocol):
    def upsert(self, clinic: Clinic, primary_location: Location) -> tuple[Clinic, bool]:
        """Persist clinic and primary location. Returns (clinic, created)."""

    def get_detail(self, clinic_id: UUID) -> ClinicDetail | None:
        """Load clinic with primary location and optional related data."""

    def list_clinics(self, query: ClinicListQuery) -> ClinicListResult:
        """Paginated clinic list with optional search filters."""

    def list_all_ids(self) -> list[UUID]:
        """Return all clinic IDs."""

    def update_locations_count(self, clinic_id: UUID, locations_count: int) -> None:
        """Update the clinic locations_count field."""

    def list_ids_with_website(self) -> list[UUID]:
        """Return clinic IDs that have a website URL."""
