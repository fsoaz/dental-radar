from pydantic import BaseModel


class ScoreBandSchema(BaseModel):
    name: str
    min: int
    max: int | None = None


class ScoringConfigResponse(BaseModel):
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBandSchema]


class UpdateScoringConfigRequest(BaseModel):
    weights: dict[str, int]
    bands: list[ScoreBandSchema]
    rescore: bool = False


class UpdateScoringConfigResponse(BaseModel):
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBandSchema]
    rescored: int = 0
