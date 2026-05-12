import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from .database import DATA_DIR

AUDIO_SUBDIR = DATA_DIR / "audio"
AUDIO_SUBDIR.mkdir(parents=True, exist_ok=True)


def save_audio_upload(project_id: int, upload: UploadFile) -> tuple[str, str]:
    """Returns (stored_relative_path, original_filename)."""
    suffix = Path(upload.filename or "audio").suffix.lower()
    if suffix not in {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".webm"}:
        suffix = ".bin"
    name = f"{project_id}_{uuid.uuid4().hex}{suffix}"
    dest = AUDIO_SUBDIR / name
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    rel = str(dest.relative_to(DATA_DIR))
    return rel, upload.filename or name
