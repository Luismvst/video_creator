"""Ensamblado final del videoclip (VideoZero v2 · Fase 5).

Toma los clips generados por `render_client` (uno por segmento), los concatena en
orden y **pega encima el audio original** de la canción con ffmpeg → `videoclip_final.mp4`.
Opcionalmente quema subtítulos con la letra a partir de `line_timings` (F1).

Sin dependencias pesadas: usa ffmpeg como subprocess. Modo `dry_run=True` (por defecto)
y entorno sin ffmpeg → devuelve el **plan y el comando** sin ejecutar, para que la fase
sea testeable y verificable sin binarios. Los helpers de construcción son puros.

Supuesto: los clips comparten códec/resolución (mismo proveedor/ajustes) → concat demuxer.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Helpers puros
# --------------------------------------------------------------------------- #

def _fmt_ts(seconds: float) -> str:
    """Segundos → 'HH:MM:SS,mmm' (formato de tiempo SRT)."""
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    s = (total_ms // 1000) % 60
    m = (total_ms // 60000) % 60
    h = total_ms // 3600000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(line_timings: list[dict[str, Any]]) -> str:
    """Construye un SRT a partir de las líneas con tiempo (start/end no nulos)."""
    timed = [
        r for r in (line_timings or [])
        if r.get("start") is not None and r.get("end") is not None
        and str(r.get("line", "")).strip()
    ]
    timed.sort(key=lambda r: float(r["start"]))
    blocks: list[str] = []
    for i, r in enumerate(timed, start=1):
        start = float(r["start"])
        end = max(float(r["end"]), start + 0.3)  # mínimo legible
        blocks.append(
            f"{i}\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{str(r['line']).strip()}\n"
        )
    return "\n".join(blocks)


def build_concat_list(clip_paths: list[str]) -> str:
    """Contenido del fichero de lista para el concat demuxer de ffmpeg.

    Normaliza a barras '/' (ffmpeg las acepta también en Windows) y escapa comillas.
    """
    lines: list[str] = []
    for p in clip_paths:
        norm = str(p).replace("\\", "/").replace("'", r"'\''")
        lines.append(f"file '{norm}'")
    return "\n".join(lines) + ("\n" if lines else "")


def build_ffmpeg_command(
    concat_list_path: str,
    audio_path: str,
    out_path: str,
    *,
    srt_path: Optional[str] = None,
    crf: int = 20,
) -> list[str]:
    """Construye el argv de ffmpeg: concat de vídeo + audio original (+ subtítulos opc.).

    - Mapea el vídeo concatenado (input 0) y el audio de la canción (input 1).
    - `-shortest` corta a la pista más corta para evitar colas mudas.
    - Con subtítulos re-encoda el vídeo (filtro `subtitles`); sin ellos copia el vídeo.
    """
    cmd: list[str] = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
    ]
    if srt_path:
        subs = str(srt_path).replace("\\", "/").replace(":", r"\:")
        cmd += ["-vf", f"subtitles='{subs}'", "-c:v", "libx264", "-crf", str(crf)]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", out_path]
    return cmd


def resolve_clip_paths(
    segments: list[dict[str, Any]], clips_dir: str
) -> list[str]:
    """Deriva las rutas de clips desde los índices de segmento (clip_001.mp4, ...),
    coherente con el naming de `render_client.render_segment`."""
    out: list[str] = []
    for s in segments:
        idx = s.get("index")
        name = f"clip_{int(idx):03d}.mp4" if isinstance(idx, int) else "clip.mp4"
        out.append(str(Path(clips_dir) / name))
    return out


# --------------------------------------------------------------------------- #
# Orquestador
# --------------------------------------------------------------------------- #

def assemble(
    *,
    out_path: str,
    audio_path: str,
    clips_dir: Optional[str] = None,
    clip_paths: Optional[list[str]] = None,
    segments: Optional[list[dict[str, Any]]] = None,
    line_timings: Optional[list[dict[str, Any]]] = None,
    subtitles: bool = False,
    dry_run: bool = True,
    work_dir: Optional[str] = None,
    timeout_sec: float = 1800.0,
) -> dict[str, Any]:
    """Ensambla el MP4 final. dry-run / sin ffmpeg → devuelve el plan sin ejecutar.

    Proporciona `clip_paths` directamente, o (`segments` + `clips_dir`) para derivarlos.
    """
    if clip_paths is None:
        if not (segments and clips_dir):
            return {"ok": False, "error": "Da clip_paths, o bien segments + clips_dir."}
        clip_paths = resolve_clip_paths(segments, clips_dir)
    if not clip_paths:
        return {"ok": False, "error": "No hay clips que ensamblar."}

    missing = [p for p in clip_paths if not Path(p).exists()]
    audio_ok = Path(audio_path).exists()
    ffmpeg_available = shutil.which("ffmpeg") is not None

    wd = Path(work_dir) if work_dir else Path(out_path).resolve().parent / "_assemble"
    concat_list_path = str(wd / "concat_list.txt")
    srt_path = str(wd / "subs.srt") if (subtitles and line_timings) else None

    concat_content = build_concat_list(clip_paths)
    srt_content = build_srt(line_timings) if srt_path else None
    command = build_ffmpeg_command(concat_list_path, audio_path, out_path, srt_path=srt_path)

    plan = {
        "n_clips": len(clip_paths),
        "missing_clips": missing,
        "audio_present": audio_ok,
        "ffmpeg_available": ffmpeg_available,
        "subtitles": bool(srt_path),
        "concat_list_path": concat_list_path,
        "srt_path": srt_path,
        "out_path": out_path,
        "command": command,
    }

    blockers: list[str] = []
    if missing:
        blockers.append(f"{len(missing)} clip(s) no existen (genera el render primero).")
    if not audio_ok:
        blockers.append("No encuentro el audio original.")
    if not ffmpeg_available:
        blockers.append("ffmpeg no está en PATH.")

    if dry_run or blockers:
        return {
            "ok": not blockers,
            "dry_run": True,
            "reason": "; ".join(blockers) if blockers else "dry-run (no se ejecutó ffmpeg).",
            **plan,
        }

    # Ejecución real
    wd.mkdir(parents=True, exist_ok=True)
    Path(concat_list_path).write_text(concat_content, encoding="utf-8")
    if srt_content is not None:
        Path(srt_path).write_text(srt_content, encoding="utf-8")
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout_sec)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"ffmpeg falló: {e}", **plan}
    if proc.returncode != 0 or not Path(out_path).exists():
        return {"ok": False, "error": f"ffmpeg rc={proc.returncode}: {proc.stderr[-500:]}", **plan}
    return {"ok": True, "dry_run": False, "out_path": out_path, **plan}
