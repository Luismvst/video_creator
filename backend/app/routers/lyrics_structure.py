from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..creative_guard import assert_song_unlocked_for_structure
from ..database import get_session
from ..lyrics_util import split_lyric_lines, validate_section_span
from ..models import LyricSection, Project, Song
from ..schemas import (
    LyricLineRead,
    LyricLinesResponse,
    LyricSectionCreate,
    LyricSectionRead,
    LyricSectionReorderBody,
    LyricSectionUpdate,
)

router = APIRouter(prefix="/projects", tags=["lyric-structure"])


def _require_project(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _song_for_project(session: Session, project_id: int) -> Song:
    _require_project(session, project_id)
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.get("/{project_id}/song/lines", response_model=LyricLinesResponse)
def get_lyric_lines(project_id: int, session: Session = Depends(get_session)):
    song = _song_for_project(session, project_id)
    raw = split_lyric_lines(song.lyrics_text)
    lines = [LyricLineRead(index=i, text=text) for i, text in enumerate(raw)]
    return LyricLinesResponse(lines=lines)


@router.post("/{project_id}/song/sections", response_model=LyricSectionRead)
def create_section(
    project_id: int,
    body: LyricSectionCreate,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_structure(song)
    try:
        validate_section_span(song.lyrics_text, body.start_line_index, body.end_line_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    existing = session.exec(select(LyricSection).where(LyricSection.song_id == song.id)).all()
    next_order = (
        body.sort_order
        if body.sort_order is not None
        else (max((s.sort_order for s in existing), default=-1) + 1)
    )

    section = LyricSection(
        song_id=song.id,
        label=body.label.strip(),
        kind=body.kind,
        sort_order=next_order,
        start_line_index=body.start_line_index,
        end_line_index=body.end_line_index,
    )
    session.add(section)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(section)
    return LyricSectionRead.model_validate(section)


@router.put("/{project_id}/song/sections/reorder", response_model=list[LyricSectionRead])
def reorder_sections(
    project_id: int,
    body: LyricSectionReorderBody,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_structure(song)
    rows = session.exec(select(LyricSection).where(LyricSection.song_id == song.id)).all()
    by_id = {r.id: r for r in rows if r.id is not None}
    if not by_id and body.section_ids:
        raise HTTPException(status_code=400, detail="No sections to reorder.")
    expected = set(by_id.keys())
    got = set(body.section_ids)
    if expected != got:
        raise HTTPException(
            status_code=400,
            detail="section_ids must list each section id exactly once for this song.",
        )
    for i, sid in enumerate(body.section_ids):
        sec = by_id[sid]
        sec.sort_order = i
        session.add(sec)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    out = session.exec(
        select(LyricSection)
        .where(LyricSection.song_id == song.id)
        .order_by(LyricSection.sort_order, LyricSection.id)
    ).all()
    return [LyricSectionRead.model_validate(r) for r in out]


@router.patch("/{project_id}/song/sections/{section_id}", response_model=LyricSectionRead)
def update_section(
    project_id: int,
    section_id: int,
    body: LyricSectionUpdate,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_structure(song)
    section = session.get(LyricSection, section_id)
    if not section or section.song_id != song.id:
        raise HTTPException(status_code=404, detail="Section not found")

    data = body.model_dump(exclude_unset=True)
    start = data.get("start_line_index", section.start_line_index)
    end = data.get("end_line_index", section.end_line_index)
    try:
        validate_section_span(song.lyrics_text, start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    for key, value in data.items():
        if key == "label" and isinstance(value, str):
            value = value.strip()
        setattr(section, key, value)

    song.updated_at = datetime.now(timezone.utc)
    session.add(section)
    session.add(song)
    session.commit()
    session.refresh(section)
    return LyricSectionRead.model_validate(section)


@router.delete("/{project_id}/song/sections/{section_id}", response_model=LyricSectionRead)
def delete_section(
    project_id: int,
    section_id: int,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_structure(song)
    section = session.get(LyricSection, section_id)
    if not section or section.song_id != song.id:
        raise HTTPException(status_code=404, detail="Section not found")
    payload = LyricSectionRead.model_validate(section)
    session.delete(section)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    return payload
