"""Orquestador end-to-end (VideoZero v2). Encadena F1→F5 en un solo flujo.

  letra (+ URL/audio)  →  [F1] tiempos de letra + análisis musical
                       →  [shots] dirección (onboarding_ai, heurístico sin key)
                       →  [F2] timeline real anclado a la música
                       →  [F4] plan de keyframes encadenados (opcional)
                       →  [F3] estimación de coste + gate de presupuesto + render
                       →  [F5] plan/ejecución de ensamblado → MP4 final

`dry_run=True` (def): no gasta, no necesita FAL_KEY ni binarios; devuelve el manifiesto
completo (tiempos, segmentos, costes, comando ffmpeg). `dry_run=False` requiere FAL_KEY
(render/keyframes) y ffmpeg (ensamblado).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .audio_ingest import ingest_and_align
from .keyframes import plan_keyframes
from .music_planner import plan_timeline
from .onboarding_ai import build_onboarding_package
from .render_client import DEFAULT_PROVIDER, DEFAULT_REROLL, estimate_render_cost, render_timeline
from .video_assembly import assemble


def run_pipeline(
    *,
    lyrics_text: str,
    url: Optional[str] = None,
    audio_file: Optional[str] = None,
    brief: str = "",
    title: Optional[str] = None,
    mood: Optional[str] = None,
    language: str = "es",
    target_duration: Optional[float] = None,
    provider: str = DEFAULT_PROVIDER,
    reroll_factor: float = DEFAULT_REROLL,
    max_budget_usd: Optional[float] = None,
    keyframes: bool = False,
    subtitles: bool = True,
    prefer_llm: bool = False,
    do_stems: bool = True,
    work_dir: str = "vz_work",
    out_path: str = "videoclip_final.mp4",
    dry_run: bool = True,
    fal_key: Optional[str] = None,
) -> dict[str, Any]:
    """Ejecuta el pipeline completo y devuelve un manifiesto JSON-serializable."""
    wd = Path(work_dir)
    clips_dir = str(wd / "clips")
    keyframes_dir = str(wd / "keyframes")

    # --- F1: audio → tiempos de letra + música -----------------------------
    ingest = ingest_and_align(
        lyrics_text=lyrics_text, url=url, audio_file=audio_file,
        work_dir=str(wd / "audio"), language=language, do_stems=do_stems,
    )
    line_timings = ingest.get("line_timings") or []
    music = ingest.get("music") or {}
    audio_path = ingest.get("wav_path")
    duration = music.get("duration_sec") or target_duration or 180.0

    # --- shots: dirección creativa (heurística sin key; LLM si prefer_llm) ---
    pkg, shots_note = build_onboarding_package(
        lyrics_text, brief, title=title, mood=mood, language=language, prefer_llm=prefer_llm,
    )
    try:
        shots = json.loads(pkg["shots_json"])
        if not isinstance(shots, list):
            shots = []
    except (json.JSONDecodeError, KeyError, TypeError):
        shots = []

    # --- F2: timeline real anclado a la música ------------------------------
    segments, timeline_source = plan_timeline(
        shots, line_timings=line_timings, music=music, total_seconds=duration, title=title,
    )

    # --- F4: plan de keyframes (opcional) -----------------------------------
    kf = None
    if keyframes:
        kf = plan_keyframes(segments, out_dir=keyframes_dir, dry_run=dry_run, fal_key=fal_key)

    # --- F3: coste + gate + render ------------------------------------------
    render = render_timeline(
        segments, provider=provider, reroll_factor=reroll_factor,
        max_budget_usd=max_budget_usd, dry_run=dry_run, fal_key=fal_key, out_dir=clips_dir,
    )

    # --- F5: ensamblado (plan o ejecución) ----------------------------------
    assembly = assemble(
        out_path=out_path, audio_path=audio_path or str(wd / "audio" / "song.wav"),
        segments=segments, clips_dir=clips_dir, line_timings=line_timings,
        subtitles=subtitles, dry_run=dry_run,
    )

    # --- Coste total agregado ------------------------------------------------
    render_est = render.get("estimate") or estimate_render_cost(
        segments, provider=provider, reroll_factor=reroll_factor
    )
    kf_usd = (kf or {}).get("estimate", {}).get("estimated_usd", 0.0) if keyframes else 0.0
    total_usd = round(float(render_est.get("estimated_usd", 0.0)) + float(kf_usd), 2)

    # --- Artefactos ----------------------------------------------------------
    artifacts: dict[str, str] = {}
    try:
        wd.mkdir(parents=True, exist_ok=True)
        (wd / "timings.json").write_text(
            json.dumps({"line_timings": line_timings, "music": music}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (wd / "segments.json").write_text(
            json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        artifacts = {
            "timings": str(wd / "timings.json"),
            "segments": str(wd / "segments.json"),
        }
    except OSError:
        artifacts = {}

    manifest = {
        "dry_run": dry_run,
        "degraded_audio": ingest.get("degraded", False),
        "audio_path": audio_path,
        "shots_note": shots_note,
        "n_shots": len(shots),
        "timeline_source": timeline_source,
        "n_segments": len(segments),
        "duration_sec": round(float(duration), 2),
        "cost": {
            "provider": provider,
            "render_usd": render_est.get("estimated_usd"),
            "keyframes_usd": kf_usd if keyframes else None,
            "total_estimated_usd": total_usd,
            "max_budget_usd": max_budget_usd,
            "over_budget": bool(render.get("aborted")),
        },
        "f1_ingest_steps": ingest.get("steps", []),
        "f3_render": {k: render.get(k) for k in ("ok", "aborted", "reason", "rendered_ok", "dry_run")},
        "f4_keyframes": (
            {"planned": len((kf or {}).get("keyframes", [])), "chain": (kf or {}).get("chain"),
             "estimate": (kf or {}).get("estimate")}
            if keyframes else None
        ),
        "f5_assembly": {k: assembly.get(k) for k in ("ok", "dry_run", "reason", "n_clips",
                                                     "missing_clips", "ffmpeg_available", "command")},
        "artifacts": artifacts,
        "out_path": out_path,
    }
    return manifest
