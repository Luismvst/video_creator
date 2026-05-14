from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session, select

from ..creative_guard import assert_song_unlocked_for_insights
from ..database import get_session
from ..lyrics_insights_engine import heuristic_insights, llm_insights, openai_configured
from ..models import LyricInsight, Project, Song
from ..schemas import (
    LyricInsightCreate,
    LyricInsightGenerateBody,
    LyricInsightGenerateResult,
    LyricInsightRead,
    LyricInsightReorderBody,
    LyricInsightUpdate,
)

router = APIRouter(prefix="/projects", tags=["lyric-insights"])


def _song_for_project(session: Session, project_id: int) -> Song:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    song = session.exec(select(Song).where(Song.project_id == project_id)).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


def _next_sort_order(session: Session, song_id: int) -> int:
    rows = session.exec(select(LyricInsight).where(LyricInsight.song_id == song_id)).all()
    return max((r.sort_order for r in rows), default=-1) + 1


def _truncate(s: str, n: int = 600) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


@router.post("/{project_id}/song/insights/generate", response_model=LyricInsightGenerateResult)
def generate_insights(
    project_id: int,
    body: Optional[LyricInsightGenerateBody] = Body(default=None),
    session: Session = Depends(get_session),
):
    opts = body or LyricInsightGenerateBody()
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_insights(song)
    lyrics = (song.lyrics_text or "").strip()
    if not lyrics:
        raise HTTPException(status_code=400, detail="Add non-empty lyrics before generating insights.")

    note: str | None = None
    engine_used = "heuristic"
    tuples: list[tuple[str, str]] = []

    if opts.mode == "heuristic":
        tuples = heuristic_insights(song.lyrics_text or "")
    elif opts.mode == "llm":
        tuples, err = llm_insights(
            song.lyrics_text or "",
            title=song.title,
            mood=song.mood,
            language=song.language,
        )
        if tuples:
            engine_used = "llm"
        else:
            raise HTTPException(status_code=502, detail=err or "LLM generation failed.")
    else:
        if openai_configured():
            tuples, err = llm_insights(
                song.lyrics_text or "",
                title=song.title,
                mood=song.mood,
                language=song.language,
            )
            if tuples:
                engine_used = "llm"
            else:
                tuples = heuristic_insights(song.lyrics_text or "")
                engine_used = "heuristic"
                note = err or "LLM failed; used heuristic fallback."
        else:
            tuples = heuristic_insights(song.lyrics_text or "")
            engine_used = "heuristic"
            note = "No OpenAI key; used heuristic engine."

    if opts.replace:
        rows = session.exec(select(LyricInsight).where(LyricInsight.song_id == song.id)).all()
        for r in rows:
            if r.source in ("heuristic", "llm"):
                session.delete(r)
        session.commit()

    start_order = _next_sort_order(session, song.id)
    created = 0
    for i, (cat, text) in enumerate(tuples):
        row = LyricInsight(
            song_id=song.id,
            category=cat,
            text=_truncate(text),
            sort_order=start_order + i,
            source=engine_used,
        )
        session.add(row)
        created += 1

    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()

    return LyricInsightGenerateResult(created_count=created, engine=engine_used, note=note)


@router.post("/{project_id}/song/insights", response_model=LyricInsightRead)
def create_insight(
    project_id: int,
    body: LyricInsightCreate,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_insights(song)
    order = body.sort_order if body.sort_order is not None else _next_sort_order(session, song.id)
    row = LyricInsight(
        song_id=song.id,
        category=body.category,
        text=_truncate(body.text),
        sort_order=order,
        source="user",
    )
    session.add(row)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    session.refresh(row)
    return LyricInsightRead.model_validate(row)


@router.put("/{project_id}/song/insights/reorder", response_model=list[LyricInsightRead])
def reorder_insights(
    project_id: int,
    body: LyricInsightReorderBody,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_insights(song)
    rows = session.exec(select(LyricInsight).where(LyricInsight.song_id == song.id)).all()
    by_id = {r.id: r for r in rows if r.id is not None}
    if not by_id and body.insight_ids:
        raise HTTPException(status_code=400, detail="No insights to reorder.")
    expected = set(by_id.keys())
    got = set(body.insight_ids)
    if expected != got:
        raise HTTPException(
            status_code=400,
            detail="insight_ids must list each insight id exactly once for this song.",
        )
    for i, iid in enumerate(body.insight_ids):
        row = by_id[iid]
        row.sort_order = i
        session.add(row)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    out = session.exec(
        select(LyricInsight)
        .where(LyricInsight.song_id == song.id)
        .order_by(LyricInsight.sort_order, LyricInsight.id)
    ).all()
    return [LyricInsightRead.model_validate(r) for r in out]


@router.patch("/{project_id}/song/insights/{insight_id}", response_model=LyricInsightRead)
def update_insight(
    project_id: int,
    insight_id: int,
    body: LyricInsightUpdate,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_insights(song)
    row = session.get(LyricInsight, insight_id)
    if not row or row.song_id != song.id:
        raise HTTPException(status_code=404, detail="Insight not found")

    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    for k, v in data.items():
        if k == "text" and isinstance(v, str):
            v = _truncate(v)
        setattr(row, k, v)
    row.source = "user"

    song.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.add(song)
    session.commit()
    session.refresh(row)
    return LyricInsightRead.model_validate(row)


@router.delete("/{project_id}/song/insights/{insight_id}", response_model=LyricInsightRead)
def delete_insight(
    project_id: int,
    insight_id: int,
    session: Session = Depends(get_session),
):
    song = _song_for_project(session, project_id)
    assert_song_unlocked_for_insights(song)
    row = session.get(LyricInsight, insight_id)
    if not row or row.song_id != song.id:
        raise HTTPException(status_code=404, detail="Insight not found")
    payload = LyricInsightRead.model_validate(row)
    session.delete(row)
    song.updated_at = datetime.now(timezone.utc)
    session.add(song)
    session.commit()
    return payload
