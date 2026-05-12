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

    audio_path: Optional[str] = None
    audio_original_filename: Optional[str] = None
    audio_rights_confirmed: bool = False

    updated_at: datetime = Field(default_factory=utcnow)

    project: Project = Relationship(back_populates="song")
