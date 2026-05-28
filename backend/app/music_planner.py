"""Planner temporal real (VideoZero v2 · Fase 2).

Sustituye el reparto ciego de `timed_segments.propose_timed_segments` cuando hay
audio analizado: ancla los cortes a los tiempos REALES de cada línea de la letra
(`line_timings` de F1), los ajusta al pulso (`beats`) y acelera el corte en las
secciones de más energía. Los segmentos son **contiguos y cubren [0, total]**
(sin huecos ni solapes), listos para `ffmpeg concat` en fases posteriores.

Entrada principal `plan_timeline()`: usa el planner musical si hay tiempos; si no,
cae al heurístico existente. Un único punto de entrada para ambos modos.

La forma del segmento es compatible con `timed_segments` (index/start_sec/end_sec/
duration_sec/shot/prompt_*), con extras `line_indices` y `source`.
"""

from __future__ import annotations

import math
from statistics import median
from typing import Any, Optional

from .music_analysis import snap_times_to_beats
from .prompt_compile import compile_prompt_markdown


# --------------------------------------------------------------------------- #
# Helpers puros
# --------------------------------------------------------------------------- #

def _to_intervals(cuts: list[float], total: float) -> list[list[float]]:
    """Puntos de corte ordenados → intervalos contiguos [cut_i, cut_{i+1}], último a `total`."""
    cuts = sorted({round(float(c), 3) for c in cuts if 0.0 <= float(c) < total})
    if not cuts or cuts[0] > 0.05:
        cuts = [0.0] + cuts
    segs: list[list[float]] = []
    for i, c in enumerate(cuts):
        end = cuts[i + 1] if i + 1 < len(cuts) else total
        if end > c:
            segs.append([c, end])
    return segs


def _merge_min(segs: list[list[float]], min_clip: float) -> list[list[float]]:
    """Absorbe segmentos más cortos que `min_clip` en el anterior (quita el corte)."""
    out: list[list[float]] = []
    for s, e in segs:
        if out and (out[-1][1] - out[-1][0]) < min_clip:
            out[-1][1] = e
        else:
            out.append([s, e])
    if len(out) >= 2 and (out[-1][1] - out[-1][0]) < min_clip:
        out[-2][1] = out.pop()[1]
    return out


def _section_energy_threshold(sections: Optional[list[dict[str, Any]]]) -> Optional[float]:
    if not sections:
        return None
    vals = [float(s.get("mean_energy", 0.0)) for s in sections]
    return median(vals) if vals else None


def _is_high_energy(t: float, sections: Optional[list[dict[str, Any]]],
                    threshold: Optional[float]) -> bool:
    if not sections or threshold is None:
        return False
    for sec in sections:
        if float(sec["start_sec"]) <= t < float(sec["end_sec"]):
            return float(sec.get("mean_energy", 0.0)) > threshold
    return False


def _split_max(
    segs: list[list[float]],
    max_clip: float,
    *,
    sections: Optional[list[dict[str, Any]]] = None,
    beats: Optional[list[float]] = None,
    snap: bool = True,
    high_energy_factor: float = 0.6,
) -> list[list[float]]:
    """Trocea segmentos largos. En secciones de alta energía usa un máximo menor
    (más cortes → corte más rápido en estribillos). Los cortes interiores se
    ajustan a beats si los hay."""
    threshold = _section_energy_threshold(sections)
    out: list[list[float]] = []
    for s, e in segs:
        eff_max = max_clip
        if _is_high_energy(s, sections, threshold):
            eff_max = max_clip * high_energy_factor
        dur = e - s
        if dur <= eff_max + 1e-6:
            out.append([s, e])
            continue
        n = max(1, math.ceil(dur / eff_max))
        step = dur / n
        pts = [s + step * k for k in range(n + 1)]
        if snap and beats:
            pts = snap_times_to_beats(pts, beats)
        pts[0], pts[-1] = s, e
        pts = sorted({round(p, 3) for p in pts})
        for k in range(len(pts) - 1):
            if pts[k + 1] > pts[k]:
                out.append([pts[k], pts[k + 1]])
    return out


def _materialize(
    segs: list[list[float]],
    shots: list[dict[str, Any]],
    line_starts: list[tuple[float, int]],
    *,
    title: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Convierte intervalos en segmentos completos: reparte los shots de forma
    uniforme (más segmentos en estribillo → más cambios de plano por segundo) y
    adjunta las líneas de letra que caen en cada uno + prompts por proveedor."""
    s_count = len(segs)
    m = len(shots)
    out: list[dict[str, Any]] = []
    for i, (s, e) in enumerate(segs):
        shot = shots[min(m - 1, (i * m) // s_count)] if m else {}
        li = [idx for (st, idx) in line_starts if s <= st < e]
        seg: dict[str, Any] = {
            "index": i + 1,
            "start_sec": round(s, 2),
            "end_sec": round(e, 2),
            "duration_sec": round(e - s, 2),
            "shot": dict(shot),
            "line_indices": li,
            "source": "music",
            "prompt_generic": compile_prompt_markdown([shot], "generic").strip() if shot else "",
            "prompt_runway": compile_prompt_markdown([shot], "runway").strip() if shot else "",
            "prompt_kling": compile_prompt_markdown([shot], "kling").strip() if shot else "",
        }
        if title:
            seg["work_title"] = title
        out.append(seg)
    return out


# --------------------------------------------------------------------------- #
# Planner musical
# --------------------------------------------------------------------------- #

def plan_segments_from_timings(
    line_timings: list[dict[str, Any]],
    shots: list[dict[str, Any]],
    *,
    total_seconds: float,
    beats: Optional[list[float]] = None,
    sections: Optional[list[dict[str, Any]]] = None,
    min_clip: float = 1.5,
    max_clip: float = 8.0,
    snap: bool = True,
    title: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Planifica segmentos anclados a los tiempos reales de la letra.

    Devuelve [] si no hay tiempos utilizables o no hay shots/duración (para que el
    caller caiga al heurístico).
    """
    timed = [r for r in line_timings if r.get("start") is not None and r.get("end") is not None]
    if not timed or not shots or not total_seconds or total_seconds <= 0:
        return []
    total = float(total_seconds)

    line_starts: list[tuple[float, int]] = []
    for r in timed:
        s = float(r["start"])
        if 0.0 <= s < total:
            line_starts.append((s, int(r["line_index"])))
    line_starts.sort()
    if not line_starts:
        return []

    cuts = [s for s, _ in line_starts]
    if snap and beats:
        cuts = sorted(set(snap_times_to_beats(cuts, beats)))

    segs = _to_intervals(cuts, total)
    segs = _merge_min(segs, min_clip)
    segs = _split_max(segs, max_clip, sections=sections, beats=beats, snap=snap)
    return _materialize(segs, shots, line_starts, title=title)


def _enforce_max_clip(segments: list[dict[str, Any]], max_clip: float) -> list[dict[str, Any]]:
    """Trocea segmentos heurísticos más largos que `max_clip` (ningún motor genera
    clips de decenas de segundos). Conserva shot y prompts, reparte el tiempo y
    re-indexa. Para el modo solo-letra (sin tiempos reales)."""
    out: list[dict[str, Any]] = []
    for seg in segments:
        s = float(seg.get("start_sec") or 0.0)
        dur = float(seg.get("duration_sec") or 0.0)
        e = float(seg.get("end_sec") or (s + dur))
        if dur <= max_clip + 1e-6 or dur <= 0:
            out.append(dict(seg))
            continue
        n = max(1, math.ceil(dur / max_clip))
        step = (e - s) / n
        for k in range(n):
            ns = round(s + step * k, 2)
            ne = round(e, 2) if k == n - 1 else round(s + step * (k + 1), 2)
            child = dict(seg)
            child["start_sec"], child["end_sec"], child["duration_sec"] = ns, ne, round(ne - ns, 2)
            out.append(child)
    for i, seg in enumerate(out, start=1):
        seg["index"] = i
    return out


def plan_timeline(
    shots: list[dict[str, Any]],
    *,
    line_timings: Optional[list[dict[str, Any]]] = None,
    music: Optional[dict[str, Any]] = None,
    total_seconds: Optional[float] = None,
    title: Optional[str] = None,
    max_clip: float = 8.0,
) -> tuple[list[dict[str, Any]], str]:
    """Punto de entrada único: planner musical si hay tiempos reales, si no heurístico.

    Devuelve (segments, source) donde source ∈ {"music", "heuristic"}.
    """
    music = music or {}
    duration = total_seconds or music.get("duration_sec")

    has_timings = bool(line_timings) and any(
        r.get("start") is not None for r in (line_timings or [])
    )
    if has_timings and duration:
        segs = plan_segments_from_timings(
            line_timings or [],
            shots,
            total_seconds=float(duration),
            beats=music.get("beats"),
            sections=music.get("sections"),
            max_clip=max_clip,
            title=title,
        )
        if segs:
            return segs, "music"

    # Fallback heurístico (sin audio o sin tiempos utilizables): reparte y luego
    # trocea para que ningún clip supere max_clip (clips generables ~5-8s).
    from .timed_segments import propose_timed_segments

    segs = propose_timed_segments(float(duration or 180.0), shots, title=title)
    segs = _enforce_max_clip(segs, max_clip)
    for s in segs:
        s.setdefault("source", "heuristic")
    return segs, "heuristic"
