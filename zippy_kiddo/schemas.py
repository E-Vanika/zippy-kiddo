from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Setting(StrEnum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class Supervision(StrEnum):
    INDEPENDENT = "independent"
    NEARBY = "nearby"
    CONTINUOUS = "continuous"


class Energy(StrEnum):
    CALM = "calm"
    MODERATE = "moderate"
    ACTIVE = "active"


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=3, le=12)
    duration_minutes: int
    setting: Setting
    supervision: Supervision
    energy: Energy
    materials: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, value: int) -> int:
        allowed = {5, 10, 15, 30, 45, 60}
        if value not in allowed:
            raise ValueError(f"duration_minutes must be one of {sorted(allowed)}")
        return value

    @field_validator("materials")
    @classmethod
    def normalise_materials(cls, values: list[str]) -> list[str]:
        normalised = []
        for value in values:
            cleaned = " ".join(value.strip().lower().split())
            if not cleaned or len(cleaned) > 40:
                raise ValueError("materials must be non-empty and at most 40 characters")
            normalised.append(cleaned)
        return sorted(set(normalised))


class Activity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    min_age: int
    max_age: int
    duration_minutes: int
    setting: list[Setting]
    energy: Energy
    supervision: Supervision
    required_materials: list[str]
    optional_materials: list[str] = Field(default_factory=list)
    steps: list[str]
    setup_minutes: int
    cleanup_minutes: int
    safety_note: str
    provenance: str
    reviewer: str


class Recommendation(BaseModel):
    activity_id: str
    title: str
    description: str
    why_it_matches: list[str]
    duration_minutes: int
    setup_minutes: int
    cleanup_minutes: int
    materials: list[str]
    steps: list[str]
    supervision: Supervision
    safety_note: str
    score: float


class RecommendationResponse(BaseModel):
    request_id: str
    ranking_mode: str
    degraded: bool
    catalogue_version: str
    model_revision: str | None
    recommendations: list[Recommendation]
    relaxable_constraints: list[str]
