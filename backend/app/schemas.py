from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .lyrics_insights_engine import INSIGHT_CATEGORIES
from .lyrics_util import PACING_PROFILES, SECTION_KINDS


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    language: Optional[str] = None
    mood: Optional[str] = None
    lyrics_text: Optional[str] = None
    target_duration_seconds: Optional[float] = None
    pacing_profile: Optional[str] = None
    audio_rights_confirmed: Optional[bool] = None
    lyrics_rights_confirmed: Optional[bool] = None
    line_timings_json: Optional[str] = None
    creative_intake_json: Optional[str] = None
    director_answers_json: Optional[str] = None
    creative_routes_json: Optional[str] = None
    selected_route_id: Optional[str] = None
    timeline_plan_json: Optional[str] = None
    scenes_json: Optional[str] = None
    shots_json: Optional[str] = None
    generation_plan_json: Optional[str] = None
    review_matrix_json: Optional[str] = None

    @field_validator("pacing_profile")
    @classmethod
    def pacing_ok(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if v not in PACING_PROFILES:
            raise ValueError(f"pacing_profile must be one of: {', '.join(sorted(PACING_PROFILES))}")
        return v


class LyricLineRead(BaseModel):
    index: int
    text: str


class LyricLinesResponse(BaseModel):
    lines: list[LyricLineRead]


class LyricSectionRead(BaseModel):
    id: int
    song_id: int
    label: str
    kind: str
    sort_order: int
    start_line_index: int
    end_line_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class LyricSectionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    kind: str = "verse"
    start_line_index: int = Field(ge=0)
    end_line_index: int = Field(ge=0)
    sort_order: Optional[int] = Field(default=None, ge=0)

    @field_validator("kind")
    @classmethod
    def kind_ok(cls, v: str) -> str:
        if v not in SECTION_KINDS:
            raise ValueError(f"kind must be one of: {', '.join(sorted(SECTION_KINDS))}")
        return v


class LyricSectionUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=120)
    kind: Optional[str] = None
    start_line_index: Optional[int] = Field(default=None, ge=0)
    end_line_index: Optional[int] = Field(default=None, ge=0)
    sort_order: Optional[int] = Field(default=None, ge=0)

    @field_validator("kind")
    @classmethod
    def kind_ok(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in SECTION_KINDS:
            raise ValueError(f"kind must be one of: {', '.join(sorted(SECTION_KINDS))}")
        return v


class LyricSectionReorderBody(BaseModel):
    section_ids: list[int] = Field(min_length=1)

    @field_validator("section_ids")
    @classmethod
    def unique_ids(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("section_ids must be unique")
        return v


class LyricInsightRead(BaseModel):
    id: int
    song_id: int
    category: str
    text: str
    sort_order: int
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class LyricInsightCreate(BaseModel):
    category: str
    text: str = Field(min_length=1, max_length=600)
    sort_order: Optional[int] = Field(default=None, ge=0)

    @field_validator("category")
    @classmethod
    def cat_ok(cls, v: str) -> str:
        if v not in INSIGHT_CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(INSIGHT_CATEGORIES))}")
        return v


class LyricInsightUpdate(BaseModel):
    category: Optional[str] = None
    text: Optional[str] = Field(default=None, min_length=1, max_length=600)
    sort_order: Optional[int] = Field(default=None, ge=0)

    @field_validator("category")
    @classmethod
    def cat_ok(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in INSIGHT_CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(INSIGHT_CATEGORIES))}")
        return v


class LyricInsightGenerateBody(BaseModel):
    mode: str = "auto"
    replace: bool = True

    @field_validator("mode")
    @classmethod
    def mode_ok(cls, v: str) -> str:
        if v not in {"auto", "heuristic", "llm"}:
            raise ValueError("mode must be auto, heuristic, or llm")
        return v


class LyricInsightGenerateResult(BaseModel):
    created_count: int
    engine: str
    note: Optional[str] = None


class LyricInsightReorderBody(BaseModel):
    insight_ids: list[int] = Field(min_length=1)

    @field_validator("insight_ids")
    @classmethod
    def unique_insight_ids(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("insight_ids must be unique")
        return v


class SongRead(BaseModel):
    id: int
    project_id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    language: Optional[str] = None
    mood: Optional[str] = None
    lyrics_text: Optional[str] = None
    target_duration_seconds: Optional[float] = None
    pacing_profile: Optional[str] = None
    audio_original_filename: Optional[str] = None
    audio_rights_confirmed: bool
    lyrics_rights_confirmed: bool
    has_audio: bool
    sections: list[LyricSectionRead] = Field(default_factory=list)
    insights: list[LyricInsightRead] = Field(default_factory=list)
    structure_warnings: list[str] = Field(default_factory=list)
    line_timings_json: Optional[str] = None
    creative_intake_json: Optional[str] = None
    director_answers_json: Optional[str] = None
    creative_routes_json: Optional[str] = None
    selected_route_id: Optional[str] = None
    creative_lock_at: Optional[datetime] = None
    creative_lock_snapshot_json: Optional[str] = None
    creative_locked: bool = False
    timeline_plan_json: Optional[str] = None
    scenes_json: Optional[str] = None
    shots_json: Optional[str] = None
    generation_plan_json: Optional[str] = None
    review_matrix_json: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentsPreviewRead(BaseModel):
    visual_bible_markdown: str
    treatment_markdown: str


class ProjectDetailRead(ProjectRead):
    song: Optional[SongRead] = None


class OnboardingApplyBriefBody(BaseModel):
    brief: str = Field(min_length=1, max_length=8000)
    mode: str = Field(default="auto", description="auto | heuristic | llm")


class OnboardingBriefResult(BaseModel):
    project: ProjectDetailRead
    hint: str


class AnalysisEnqueueResult(BaseModel):
    status: str
    message: str
    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggested next steps in the lyrics-first workflow (stub pipeline; no jobs enqueued).",
    )
