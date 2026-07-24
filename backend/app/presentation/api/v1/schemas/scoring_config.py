from pydantic import BaseModel, field_validator, model_validator


class ScoreBandSchema(BaseModel):
    name: str
    min: int
    max: int | None = None

    @model_validator(mode="after")
    def _validate_range(self) -> "ScoreBandSchema":
        if self.min < 0:
            raise ValueError("band min must be >= 0")
        if self.max is not None and self.max < self.min:
            raise ValueError("band max must be >= min")
        return self


class ScoringConfigResponse(BaseModel):
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBandSchema]


class UpdateScoringConfigRequest(BaseModel):
    weights: dict[str, int]
    bands: list[ScoreBandSchema]
    rescore: bool = False

    @field_validator("weights")
    @classmethod
    def _validate_weights(cls, value: dict[str, int]) -> dict[str, int]:
        negative = {key: val for key, val in value.items() if val < 0}
        if negative:
            raise ValueError(f"weights must be >= 0, got negative values: {negative}")
        return value

    @field_validator("bands")
    @classmethod
    def _validate_bands(cls, value: list[ScoreBandSchema]) -> list[ScoreBandSchema]:
        if not value:
            raise ValueError("bands must not be empty")
        return value


class UpdateScoringConfigResponse(BaseModel):
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBandSchema]
    rescored: int = 0
