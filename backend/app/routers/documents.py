from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..document_templates import build_treatment_markdown, build_visual_bible_markdown
from ..json_fields import parse_json_optional
from ..models import Project, Song
from ..schemas import DocumentsPreviewRead
from .projects import _song_read

router = APIRouter(prefix="/projects", tags=["documents"])


def _routes_list(blob: str | None) -> list[dict[str, Any]]:
    data = parse_json_optional(blob, {})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        r = data.get("routes")
        if isinstance(r, list):
            return r
    return []


@router.get("/{project_id}/documents/preview", response_model=DocumentsPreviewRead)
def documents_preview(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    sr = _song_read(session, song)
    locked = sr.creative_locked
    sections: list[dict[str, Any]] = []
    insights: list[dict[str, Any]] = []
    title = sr.title
    artist = sr.artist
    pacing = sr.pacing_profile
    intake: dict[str, Any] = {"reference_notes": "", "style_attributes": []}
    director: dict[str, Any] = {}
    routes: list[dict[str, Any]] = []
    selected_route_id = sr.selected_route_id

    if locked and sr.creative_lock_snapshot_json:
        snap = parse_json_optional(sr.creative_lock_snapshot_json, {})
        song_snap = snap.get("song") if isinstance(snap.get("song"), dict) else {}
        sections = snap.get("sections") if isinstance(snap.get("sections"), list) else []
        insights = snap.get("insights") if isinstance(snap.get("insights"), list) else []
        title = song_snap.get("title", title)
        artist = song_snap.get("artist", artist)
        pacing = song_snap.get("pacing_profile", pacing)
        intake = parse_json_optional(song_snap.get("creative_intake_json"), intake)
        if not isinstance(intake, dict):
            intake = {"reference_notes": "", "style_attributes": []}
        director = parse_json_optional(song_snap.get("director_answers_json"), {})
        if not isinstance(director, dict):
            director = {}
        routes = _routes_list(song_snap.get("creative_routes_json"))
        selected_route_id = song_snap.get("selected_route_id", selected_route_id)
    else:
        sections = [s.model_dump(mode="json") for s in sr.sections]
        insights = [i.model_dump(mode="json") for i in sr.insights]
        intake = parse_json_optional(song.creative_intake_json, intake)
        if not isinstance(intake, dict):
            intake = {"reference_notes": "", "style_attributes": []}
        director = parse_json_optional(song.director_answers_json, {})
        if not isinstance(director, dict):
            director = {}
        routes = _routes_list(song.creative_routes_json)

    vb = build_visual_bible_markdown(
        title=title,
        artist=artist,
        pacing_profile=pacing,
        sections=sections,
        insights=insights,
        intake=intake,
        locked=locked,
    )
    tr = build_treatment_markdown(
        title=title,
        artist=artist,
        pacing_profile=pacing,
        sections=sections,
        director_answers=director,
        routes=routes,
        selected_route_id=selected_route_id,
        locked=locked,
    )
    return DocumentsPreviewRead(visual_bible_markdown=vb, treatment_markdown=tr)
