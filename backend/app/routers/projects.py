from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from ..database import get_session
from ..models import LyricInsight, LyricSection, Project, Song
from ..schemas import (
    AnalysisEnqueueResult,
    LyricInsightRead,
    LyricSectionRead,
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
    SongRead,
    SongUpdate,
)
from ..storage import save_audio_upload
from ..json_fields import validate_json_blob
from ..lyrics_util import structure_warnings

router = APIRouter(prefix="/projects", tags=["projects"])

_LOCK_PATCH_BLOCKLIST = frozenset(
    {
        "lyrics_text",
        "line_timings_json",
        "creative_intake_json",
        "director_answers_json",
        "creative_routes_json",
        "selected_route_id",
        "pacing_profile",
        "timeline_plan_json",
        "scenes_json",
        "shots_json",
        "generation_plan_json",
        "review_matrix_json",
    }
)


def _song_read(session: Session, song: Song) -> SongRead:
    sections = session.exec(
        select(LyricSection)
        .where(LyricSection.song_id == song.id)
        .order_by(LyricSection.sort_order, LyricSection.id)
    ).all()
    section_models = [LyricSectionRead.model_validate(r) for r in sections]
    insights = session.exec(
        select(LyricInsight)
        .where(LyricInsight.song_id == song.id)
        .order_by(LyricInsight.sort_order, LyricInsight.id)
    ).all()
    insight_models = [LyricInsightRead.model_validate(r) for r in insights]
    warns = structure_warnings(song.lyrics_text, list(sections))
    return SongRead(
        id=song.id,
        project_id=song.project_id,
        title=song.title,
        artist=song.artist,
        language=song.language,
        mood=song.mood,
        lyrics_text=song.lyrics_text,
        target_duration_seconds=song.target_duration_seconds,
        pacing_profile=song.pacing_profile,
        audio_original_filename=song.audio_original_filename,
        audio_rights_confirmed=song.audio_rights_confirmed,
        lyrics_rights_confirmed=song.lyrics_rights_confirmed,
        has_audio=bool(song.audio_path),
        sections=section_models,
        insights=insight_models,
        structure_warnings=warns,
        line_timings_json=song.line_timings_json,
        creative_intake_json=song.creative_intake_json,
        director_answers_json=song.director_answers_json,
        creative_routes_json=song.creative_routes_json,
        selected_route_id=song.selected_route_id,
        creative_lock_at=song.creative_lock_at,
        creative_lock_snapshot_json=song.creative_lock_snapshot_json,
        creative_locked=bool(song.creative_lock_at),
        timeline_plan_json=song.timeline_plan_json,
        scenes_json=song.scenes_json,
        shots_json=song.shots_json,
        generation_plan_json=song.generation_plan_json,
        review_matrix_json=song.review_matrix_json,
        updated_at=song.updated_at,
    )


def _project_detail(session: Session, project: Project, song: Song | None) -> ProjectDetailRead:
    return ProjectDetailRead(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        song=_song_read(session, song) if song else None,
    )


@router.post("", response_model=ProjectDetailRead)
def create_project(body: ProjectCreate, session: Session = Depends(get_session)):
    project = Project(name=body.name.strip())
    session.add(project)
    session.commit()
    session.refresh(project)
    song = Song(project_id=project.id)
    session.add(song)
    session.commit()
    session.refresh(song)
    return _project_detail(session, project, song)


@router.get("", response_model=list[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    rows = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    return [ProjectRead.model_validate(r) for r in rows]


@router.get("/{project_id}", response_model=ProjectDetailRead)
def get_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    return _project_detail(session, project, song)


@router.patch("/{project_id}/song", response_model=ProjectDetailRead)
def update_song(project_id: int, body: SongUpdate, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    data = body.model_dump(exclude_unset=True)
    if song.creative_lock_at and (set(data) & _LOCK_PATCH_BLOCKLIST):
        raise HTTPException(
            status_code=400,
            detail="Creative Lock is active. POST /projects/{id}/creative/unlock before changing lyrics, pacing, timings, intake, routes or plan JSON.",
        )
    for k, v in data.items():
        validate_json_blob(k, v)
        setattr(song, k, v)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    session.refresh(project)
    return _project_detail(session, project, song)


@router.post("/{project_id}/song/audio", response_model=ProjectDetailRead)
async def upload_audio(
    project_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if song.creative_lock_at:
        raise HTTPException(
            status_code=400,
            detail="Creative Lock is active. Unlock before replacing the audio file.",
        )
    rel, orig = save_audio_upload(project_id, file)
    song.audio_path = rel
    song.audio_original_filename = orig
    song.audio_rights_confirmed = False
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    return _project_detail(session, project, song)


@router.post("/{project_id}/analysis/enqueue", response_model=AnalysisEnqueueResult)
def enqueue_analysis_stub(project_id: int, session: Session = Depends(get_session)):
    """Lyrics-first gate + optional audio rights. Phase 2+ will replace stub with real pipeline."""
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if not song.lyrics_text or not str(song.lyrics_text).strip():
        raise HTTPException(status_code=400, detail="Add non-empty lyrics before starting the creative pipeline.")
    if not song.lyrics_rights_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirm you have rights to use these lyrics (lyrics_rights_confirmed) before continuing.",
        )
    if song.audio_path and not song.audio_rights_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Audio file present: confirm you have rights to use this audio (audio_rights_confirmed) before audio processing.",
        )

    n_sections = len(session.exec(select(LyricSection).where(LyricSection.song_id == song.id)).all())
    n_insights = len(session.exec(select(LyricInsight).where(LyricInsight.song_id == song.id)).all())
    recommendations: list[str] = []
    if n_sections == 0:
        recommendations.append(
            "Define al menos una sección de letra (STR-01) para anclar timeline y shot list a la estructura.",
        )
    if n_insights == 0:
        recommendations.append(
            "Genera o añade ideas visuales (LYR-02); enriquecen la Visual Bible y los exports.",
        )
    if not song.creative_lock_at:
        recommendations.append(
            "Cuando cierres dirección (intake, cuestionario, rutas), aplica Creative Lock antes de producir fuera de la app.",
        )
    if not song.shots_json or not str(song.shots_json).strip():
        recommendations.append(
            "Completa shots_json en la pestaña Plan para CSV/JSON de planos y prompts más útiles.",
        )
    if not song.generation_plan_json or not str(song.generation_plan_json).strip():
        recommendations.append(
            "Opcional: rellena generation_plan_json con pasos de producción (GEN-01).",
        )

    return AnalysisEnqueueResult(
        status="accepted_stub",
        message="Lyrics-first pipeline accepted (stub). No async jobs: use exports and external video tools.",
        recommendations=recommendations,
    )
