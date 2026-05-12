from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
    audio_rights_confirmed: Optional[bool] = None


class SongRead(BaseModel):
    id: int
    project_id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    language: Optional[str] = None
    mood: Optional[str] = None
    lyrics_text: Optional[str] = None
    audio_original_filename: Optional[str] = None
    audio_rights_confirmed: bool
    has_audio: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailRead(ProjectRead):
    song: Optional[SongRead] = None


class AnalysisEnqueueResult(BaseModel):
    status: str
    message: str
