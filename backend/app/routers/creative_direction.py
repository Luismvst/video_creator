from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..lyrics_util import structure_warnings
from ..models import LyricInsight, LyricSection, Project, Song
from ..schemas import LyricInsightRead, LyricSectionRead, ProjectDetailRead
from .projects import _project_detail

router = APIRouter(prefix="/projects", tags=["creative-direction"])


def _song_for_project(session: Session, project_id: int) -> Song:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


def _build_lock_snapshot(session: Session, song: Song) -> str:
    sections = session.exec(
        select(LyricSection)
        .where(LyricSection.song_id == song.id)
        .order_by(LyricSection.sort_order, LyricSection.id)
    ).all()
    insights = session.exec(
        select(LyricInsight)
        .where(LyricInsight.song_id == song.id)
        .order_by(LyricInsight.sort_order, LyricInsight.id)
    ).all()
    snap = {
        "song": {
            "title": song.title,
            "artist": song.artist,
            "language": song.language,
            "mood": song.mood,
            "pacing_profile": song.pacing_profile,
            "lyrics_text": song.lyrics_text,
            "line_timings_json": song.line_timings_json,
            "creative_intake_json": song.creative_intake_json,
            "director_answers_json": song.director_answers_json,
            "creative_routes_json": song.creative_routes_json,
            "selected_route_id": song.selected_route_id,
            "timeline_plan_json": song.timeline_plan_json,
            "scenes_json": song.scenes_json,
            "shots_json": song.shots_json,
            "generation_plan_json": song.generation_plan_json,
            "review_matrix_json": song.review_matrix_json,
        },
        "sections": [LyricSectionRead.model_validate(s).model_dump(mode="json") for s in sections],
        "insights": [LyricInsightRead.model_validate(i).model_dump(mode="json") for i in insights],
    }
    return json.dumps(snap, ensure_ascii=False)


@router.post("/{project_id}/creative/lock", response_model=ProjectDetailRead)
def lock_creative(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = _song_for_project(session, project_id)
    if song.creative_lock_at:
        session.refresh(project)
        return _project_detail(session, project, song)

    if not song.lyrics_rights_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirm lyrics rights (lyrics_rights_confirmed) before Creative Lock.",
        )
    sections = session.exec(select(LyricSection).where(LyricSection.song_id == song.id)).all()
    warns = structure_warnings(song.lyrics_text or "", list(sections))
    if warns:
        raise HTTPException(
            status_code=400,
            detail="Resolve structure_warnings before Creative Lock: " + "; ".join(warns),
        )

    song.creative_lock_at = datetime.now(timezone.utc)
    song.creative_lock_snapshot_json = _build_lock_snapshot(session, song)
    song.updated_at = song.creative_lock_at
    session.add(song)
    session.commit()
    session.refresh(song)
    session.refresh(project)
    return _project_detail(session, project, song)


@router.post("/{project_id}/creative/unlock", response_model=ProjectDetailRead)
def unlock_creative(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = _song_for_project(session, project_id)
    song.creative_lock_at = None
    song.creative_lock_snapshot_json = None
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    session.refresh(project)
    return _project_detail(session, project, song)
