from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow)

    song: Optional["Song"] = Relationship(back_populates="project", sa_relationship_kwargs={"uselist": False})


class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", unique=True)

    title: Optional[str] = None
    artist: Optional[str] = None
    language: Optional[str] = None
    mood: Optional[str] = None
    lyrics_text: Optional[str] = None

    # Primary clock when no audio: optional user-provided target length in seconds.
    target_duration_seconds: Optional[float] = None

    # STR-02: guided pacing profile (no DSP); influences later planning defaults.
    pacing_profile: Optional[str] = None

    audio_path: Optional[str] = None
    audio_original_filename: Optional[str] = None
    audio_rights_confirmed: bool = False
    lyrics_rights_confirmed: bool = False

    # ALN-01: optional per-line timings as JSON: [{ "line_index": int, "start_sec": float|null, "end_sec": float|null }, ...]
    line_timings_json: Optional[str] = None

    # CRE-01 / DIR-01 / DIR-02 — JSON blobs (MVP); lock stores frozen snapshot.
    creative_intake_json: Optional[str] = None
    director_answers_json: Optional[str] = None
    creative_routes_json: Optional[str] = None
    selected_route_id: Optional[str] = None
    creative_lock_at: Optional[datetime] = None
    creative_lock_snapshot_json: Optional[str] = None

    # PLN-* MVP: planificación serializada (hasta tablas dedicadas en iteración siguiente)
    timeline_plan_json: Optional[str] = None
    scenes_json: Optional[str] = None
    shots_json: Optional[str] = None
    generation_plan_json: Optional[str] = None
    review_matrix_json: Optional[str] = None

    updated_at: datetime = Field(default_factory=utcnow)

    project: Project = Relationship(back_populates="song")
    sections: list["LyricSection"] = Relationship(back_populates="song")
    insights: list["LyricInsight"] = Relationship(back_populates="song")


class LyricSection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    song_id: int = Field(foreign_key="song.id", index=True)
    label: str = Field(min_length=1, max_length=120)
    kind: str = Field(default="verse", max_length=32)
    sort_order: int = Field(default=0, ge=0)
    start_line_index: int = Field(default=0, ge=0)
    end_line_index: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    song: Song = Relationship(back_populates="sections")


class LyricInsight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    song_id: int = Field(foreign_key="song.id", index=True)
    category: str = Field(max_length=32)
    text: str = Field(default="", max_length=2000)
    sort_order: int = Field(default=0, ge=0)
    source: str = Field(default="user", max_length=16)
    created_at: datetime = Field(default_factory=utcnow)

    song: Song = Relationship(back_populates="insights")
