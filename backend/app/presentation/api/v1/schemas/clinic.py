from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DiscoverClinicsRequest(BaseModel):
    query: str = Field(min_length=1, examples=["dentist in Lisbon"])


class DiscoverClinicsResponse(BaseModel):
    ingested: int
    created: int
    updated: int


class ClinicListItemResponse(BaseModel):
    id: UUID
    name: str
    city: str | None = None
    state: str | None = None
    score: int | None = None
    priority: str | None = None
    growth_probability: int | None = None


class ClinicListResponse(BaseModel):
    data: list[ClinicListItemResponse]
    page: int
    page_size: int
    total: int


class AddressResponse(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class SignalResponse(BaseModel):
    type: str
    applied_weight: int
    evidence: str | None = None
    confidence: float
    detected_at: datetime | None = None


class DetectSignalsResponse(BaseModel):
    detected: int
    signals: list[SignalResponse]
    skipped: bool = False
    skip_reason: str | None = None


class SignalListResponse(BaseModel):
    data: list[SignalResponse]


class ScoreResponse(BaseModel):
    total: int
    priority: str
    breakdown: dict[str, int]
    config_version: int | None = None


class ComputeScoreResponse(BaseModel):
    clinic_id: UUID
    total: int
    priority: str
    breakdown: dict[str, int]
    config_version: int


class EnrichmentResponse(BaseModel):
    growth_probability: int | None = None
    technology_maturity: int | None = None
    marketing_sophistication: int | None = None
    expansion_probability: int | None = None
    explanation: str | None = None


class EnrichClinicResponse(BaseModel):
    clinic_id: UUID
    growth_probability: int
    technology_maturity: int
    marketing_sophistication: int
    expansion_probability: int
    explanation: str
    provider: str
    model: str
    prompt_version: str
    skipped: bool = False
    skip_reason: str | None = None


class ClinicDetailResponse(BaseModel):
    id: UUID
    name: str
    place_id: str
    address: AddressResponse | None = None
    phone: str | None = None
    website: str | None = None
    google_rating: float | None = None
    google_review_count: int
    locations_count: int
    social_urls: list[str]
    signals: list[SignalResponse]
    score: ScoreResponse | None = None
    enrichment: EnrichmentResponse | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
