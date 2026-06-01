from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..json_fields import validate_json_blob
from ..lyrics_insights_engine import openai_configured
from ..lyrics_util import validate_section_span
from ..models import LyricSection, Project, Song
from ..onboarding_ai import build_onboarding_package, suggest_section_spans
from ..schemas import OnboardingApplyBriefBody, OnboardingBriefResult, ProjectDetailRead
from .projects import _project_detail

router = APIRouter(prefix="/projects", tags=["onboarding"])


def _song_for_project(session: Session, project_id: int) -> Song:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.post("/{project_id}/song/onboarding/apply-brief", response_model=OnboardingBriefResult)
def apply_onboarding_brief(
    project_id: int,
    body: OnboardingApplyBriefBody,
    session: Session = Depends(get_session),
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = _song_for_project(session, project_id)
    if song.creative_lock_at:
        raise HTTPException(status_code=400, detail="Desbloquea la dirección creativa antes de regenerar el brief.")
    lyrics = (song.lyrics_text or "").strip()
    if not lyrics:
        raise HTTPException(status_code=400, detail="Guarda la letra en el paso anterior antes de generar dirección.")

    mode = (body.mode or "auto").strip().lower()
    if mode not in ("auto", "heuristic", "llm"):
        raise HTTPException(status_code=400, detail="mode must be auto, heuristic or llm")

    prefer_llm = mode == "llm" or (mode == "auto" and openai_configured())
    pkg, hint = build_onboarding_package(
        lyrics,
        body.brief,
        title=song.title,
        mood=song.mood,
        language=song.language,
        prefer_llm=prefer_llm,
    )
    for k, v in pkg.items():
        validate_json_blob(k, v)
        setattr(song, k, v)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    session.refresh(project)
    return OnboardingBriefResult(project=_project_detail(session, project, song), hint=hint)


@router.post("/{project_id}/song/onboarding/apply-sections", response_model=ProjectDetailRead)
def apply_onboarding_sections(
    project_id: int,
    session: Session = Depends(get_session),
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = _song_for_project(session, project_id)
    if song.creative_lock_at:
        raise HTTPException(status_code=400, detail="Desbloquea antes de reemplazar secciones.")
    lyrics = song.lyrics_text or ""
    if not str(lyrics).strip():
        raise HTTPException(status_code=400, detail="Añade letra antes de sugerir secciones.")

    spans = suggest_section_spans(lyrics)
    if not spans:
        raise HTTPException(status_code=400, detail="No se pudieron inferir secciones (letra vacía).")

    for label, kind, a, b in spans:
        try:
            validate_section_span(lyrics, a, b)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    existing = session.exec(select(LyricSection).where(LyricSection.song_id == song.id)).all()
    for row in existing:
        session.delete(row)
    session.commit()

    for i, (label, kind, a, b) in enumerate(spans):
        sec = LyricSection(
            song_id=song.id,
            label=label,
            kind=kind,
            sort_order=i,
            start_line_index=a,
            end_line_index=b,
        )
        session.add(sec)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    session.refresh(project)
    return _project_detail(session, project, song)
