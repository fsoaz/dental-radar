from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator


@dataclass
class SignalSummary:
    type: str
    evidence: str | None = None


@dataclass
class ClinicAIInput:
    name: str
    site_text: str
    signals: list[SignalSummary]
    rating: float | None
    reviews: int
    locations_count: int


class EnrichmentResult(BaseModel):
    growth_probability: int = Field(ge=0, le=100)
    technology_maturity: int = Field(ge=0, le=100)
    marketing_sophistication: int = Field(ge=0, le=100)
    expansion_probability: int = Field(ge=0, le=100)
    explanation: str = Field(max_length=280)

    @field_validator(
        "growth_probability",
        "technology_maturity",
        "marketing_sophistication",
        "expansion_probability",
        mode="before",
    )
    @classmethod
    def clamp_score(cls, value: object) -> int:
        if value is None:
            return 0
        return max(0, min(100, int(value)))

    @field_validator("explanation", mode="before")
    @classmethod
    def truncate_explanation(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value)[:280]


@dataclass
class LLMCompletion:
    provider: str
    model: str
    prompt_version: str
    result: EnrichmentResult
