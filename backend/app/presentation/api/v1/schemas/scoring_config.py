from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.value_objects.priority import PriorityLevel
from app.domain.value_objects.signal_type import SignalType

PriorityBandName = Literal["COLD", "WARM", "HOT", "IMMEDIATE"]
REQUIRED_WEIGHT_KEYS = {member.value for member in SignalType}
MAX_WEIGHT = 1000
MAX_BAND_BOUND = 1_000_000


class ScoreBandSchema(BaseModel):
    """Request band with semantic validation."""

    name: PriorityBandName
    min: int = Field(ge=0, le=MAX_BAND_BOUND)
    max: int | None = Field(default=None, ge=0, le=MAX_BAND_BOUND)

    @model_validator(mode="after")
    def _validate_range(self) -> "ScoreBandSchema":
        if self.max is not None and self.max < self.min:
            raise ValueError("band max must be >= min")
        return self


class ScoreBandResponseSchema(BaseModel):
    """Response band — no enum constraint so a legacy bad row can still be read."""

    name: str
    min: int
    max: int | None = None


class ScoringConfigResponse(BaseModel):
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBandResponseSchema]
    rescore_job: "RescoreJobResponse | None" = None


class UpdateScoringConfigRequest(BaseModel):
    weights: dict[str, int]
    bands: list[ScoreBandSchema]
    rescore: bool = False

    @field_validator("weights")
    @classmethod
    def _validate_weights(cls, value: dict[str, int]) -> dict[str, int]:
        missing = sorted(REQUIRED_WEIGHT_KEYS - set(value))
        if missing:
            raise ValueError(
                f"weights must include every signal type; missing: {', '.join(missing)}"
            )
        unknown = sorted(set(value) - REQUIRED_WEIGHT_KEYS)
        if unknown:
            raise ValueError(f"unknown weight keys: {', '.join(unknown)}")
        out_of_range = {key: val for key, val in value.items() if val < 0 or val > MAX_WEIGHT}
        if out_of_range:
            raise ValueError(f"weights must be between 0 and {MAX_WEIGHT}, got: {out_of_range}")
        return value

    @field_validator("bands")
    @classmethod
    def _validate_bands(cls, value: list[ScoreBandSchema]) -> list[ScoreBandSchema]:
        if not value:
            raise ValueError("bands must not be empty")

        names = [band.name for band in value]
        if len(names) != len(set(names)):
            raise ValueError("band names must be unique")

        # Contiguous, non-overlapping coverage from 0 to unbounded.
        ordered = sorted(value, key=lambda band: band.min)
        if ordered[0].min != 0:
            raise ValueError("bands must start at min=0")

        for index, band in enumerate(ordered):
            if band.name not in {level.value for level in PriorityLevel}:
                raise ValueError(f"invalid band name: {band.name}")
            if index < len(ordered) - 1:
                if band.max is None:
                    raise ValueError("only the final band may have max=null")
                next_band = ordered[index + 1]
                if band.max + 1 != next_band.min:
                    raise ValueError(
                        f"bands leave a gap or overlap between {band.max} and {next_band.min}"
                    )
            elif band.max is not None:
                raise ValueError("final band must be unbounded (max=null)")

        return ordered


class UpdateScoringConfigResponse(BaseModel):
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBandResponseSchema]
    rescore_job: "RescoreJobResponse | None" = None


class RescoreJobResponse(BaseModel):
    id: UUID
    config_version: int
    status: Literal["queued", "running", "succeeded", "failed"]
    rescored: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None
