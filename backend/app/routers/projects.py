from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from ..database import get_session
from ..models import Project, Song
from ..schemas import (
    AnalysisEnqueueResult,
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
    SongRead,
    SongUpdate,
)
from ..storage import save_audio_upload

router = APIRouter(prefix="/projects", tags=["projects"])


def _song_read(song: Song) -> SongRead:
    return SongRead(
        id=song.id,
        project_id=song.project_id,
        title=song.title,
        artist=song.artist,
        language=song.language,
        mood=song.mood,
        lyrics_text=song.lyrics_text,
        audio_original_filename=song.audio_original_filename,
        audio_rights_confirmed=song.audio_rights_confirmed,
        has_audio=bool(song.audio_path),
        updated_at=song.updated_at,
    )


def _project_detail(project: Project, song: Song | None) -> ProjectDetailRead:
    return ProjectDetailRead(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        song=_song_read(song) if song else None,
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
    return _project_detail(project, song)


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
    return _project_detail(project, song)


@router.patch("/{project_id}/song", response_model=ProjectDetailRead)
def update_song(project_id: int, body: SongUpdate, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(song, k, v)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    session.refresh(project)
    return _project_detail(project, song)


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
    rel, orig = save_audio_upload(project_id, file)
    song.audio_path = rel
    song.audio_original_filename = orig
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(song)
    return _project_detail(project, song)


@router.post("/{project_id}/analysis/enqueue", response_model=AnalysisEnqueueResult)
def enqueue_analysis_stub(project_id: int, session: Session = Depends(get_session)):
    """OPS-01 gate + audio presence. Phase 2 will replace stub with real job."""
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if not song.audio_path:
        raise HTTPException(status_code=400, detail="Upload audio before requesting analysis.")
    if not song.audio_rights_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirm you have rights to use this audio (audio_rights_confirmed) before analysis.",
        )
    return AnalysisEnqueueResult(
        status="accepted_stub",
        message="Rights confirmed and audio present. Analysis job will run in Phase 2.",
    )
