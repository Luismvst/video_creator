from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from starlette.responses import Response

from ..database import get_session
from ..document_templates import build_treatment_markdown, build_visual_bible_markdown
from ..json_fields import parse_json_optional
from ..models import Project, Song
from ..prompt_compile import build_generation_plan_markdown, compile_prompt_markdown
from .projects import _song_read

router = APIRouter(prefix="/projects", tags=["export"])


def _song_for_project(session: Session, project_id: int) -> Song:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


def _shots_raw_resolved(song: Song) -> str | None:
    if song.creative_lock_at and song.creative_lock_snapshot_json:
        snap = parse_json_optional(song.creative_lock_snapshot_json, {})
        song_snap = snap.get("song") if isinstance(snap.get("song"), dict) else {}
        return song_snap.get("shots_json") or song.shots_json
    return song.shots_json


def shots_list_from_song(song: Song) -> list[dict[str, Any]]:
    data = parse_json_optional(_shots_raw_resolved(song), [])
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def _routes_list(blob: str | None) -> list[dict[str, Any]]:
    data = parse_json_optional(blob, {})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        r = data.get("routes")
        if isinstance(r, list):
            return r
    return []


def _bundle_parts(session: Session, song: Song) -> tuple[str, str, str, str]:
    locked = bool(song.creative_lock_at)
    sections: list[dict[str, Any]] = []
    insights: list[dict[str, Any]] = []
    title = song.title
    artist = song.artist
    pacing = song.pacing_profile
    intake: dict[str, Any] = {"reference_notes": "", "style_attributes": []}
    director: dict[str, Any] = {}
    routes: list[dict[str, Any]] = []
    selected_route_id = song.selected_route_id
    gen_raw = song.generation_plan_json

    if locked and song.creative_lock_snapshot_json:
        snap = parse_json_optional(song.creative_lock_snapshot_json, {})
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
        gen_raw = song_snap.get("generation_plan_json", gen_raw)
    else:
        sr = _song_read(session, song)
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
    steps = parse_json_optional(gen_raw, [])
    if not isinstance(steps, list):
        steps = []
    gen_md = build_generation_plan_markdown(steps)
    shots = shots_list_from_song(song)
    return vb, tr, gen_md, compile_prompt_markdown(shots, "generic")


@router.get("/{project_id}/export/bundle.md")
def export_bundle_md(project_id: int, session: Session = Depends(get_session)):
    song = _song_for_project(session, project_id)
    vb, tr, gen_md, prompts = _bundle_parts(session, song)
    body = (
        "# VideoZero — export bundle\n\n"
        + vb
        + "\n\n---\n\n"
        + tr
        + "\n\n---\n\n"
        + gen_md
        + "\n\n---\n\n# Prompts (genérico)\n\n"
        + prompts
    )
    return Response(
        content=body,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="videozero-{project_id}-bundle.md"',
        },
    )


@router.get("/{project_id}/export/prompts.md")
def export_prompts_md(
    project_id: int,
    provider: str = Query("generic", description="generic | runway | kling"),
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    shots = shots_list_from_song(song)
    body = compile_prompt_markdown(shots, provider)
    safe = "".join(c if c.isalnum() else "-" for c in provider)[:32]
    return Response(
        content=body,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="videozero-{project_id}-prompts-{safe}.md"',
        },
    )


@router.get("/{project_id}/export/shots.json")
def export_shots_json(project_id: int, session: Session = Depends(get_session)):
    song = _song_for_project(session, project_id)
    shots = shots_list_from_song(song)
    body = json.dumps(shots, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="videozero-{project_id}-shots.json"',
        },
    )


@router.get("/{project_id}/export/shots.csv")
def export_shots_csv(project_id: int, session: Session = Depends(get_session)):
    song = _song_for_project(session, project_id)
    shots = shots_list_from_song(song)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["index", "slug", "camera", "action", "notes"])
    for i, sh in enumerate(shots, start=1):
        w.writerow(
            [
                i,
                sh.get("slug", ""),
                sh.get("camera", ""),
                sh.get("action", ""),
                sh.get("notes", ""),
            ],
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="videozero-{project_id}-shots.csv"',
        },
    )
