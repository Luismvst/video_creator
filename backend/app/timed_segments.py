"""Propone duraciones por escena/plano a partir de shots y duración total de canción."""

from __future__ import annotations

import json
from typing import Any, Optional

from .prompt_compile import compile_prompt_markdown


def _weights_for_count(n: int) -> list[float]:
    if n <= 0:
        return []
    if n == 1:
        return [1.0]
    w = [1.0] * n
    w[0] *= 1.2
    w[-1] *= 1.1
    mid = n // 2
    if n >= 3:
        w[mid] *= 1.05
    return w


def propose_timed_segments(
    total_seconds: float,
    shots: list[dict[str, Any]],
    *,
    title: Optional[str] = None,
    bible: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """
    Reparte total_seconds entre shots con pesos heurísticos (respiración narrativa).
    Cada segmento: start_sec, end_sec, duration_sec, shot, prompts por proveedor.

    Si se pasa `bible` (Biblia visual DIRQ-01), se inyecta en cada prompt por capas y la
    duración real del segmento entra en la capa técnica del prompt.
    """
    total = max(0.0, float(total_seconds))
    if not shots or total <= 0:
        return []

    n = len(shots)
    weights = _weights_for_count(n)
    s = sum(weights)
    raw = [total * (wi / s) for wi in weights]

    # Redondeo a décimas y ajuste fino para sumar exacto (evita 179.9 vs 180)
    tenths = [round(x, 1) for x in raw]
    drift = round(total - sum(tenths), 1)
    if abs(drift) >= 0.05 and tenths:
        tenths[-1] = round(tenths[-1] + drift, 1)

    out: list[dict[str, Any]] = []
    t0 = 0.0
    for i, sh in enumerate(shots):
        dur = max(0.1, tenths[i])
        t1 = t0 + dur
        if i == n - 1:
            t1 = total
            dur = round(t1 - t0, 1)
        # El prompt por capas incluye la duración real del plano en su capa técnica.
        sh_timed = {**sh, "duration_sec": round(dur, 1)}
        seg = {
            "index": i + 1,
            "start_sec": round(t0, 1),
            "end_sec": round(t1, 1),
            "duration_sec": round(dur, 1),
            "shot": dict(sh),
            "prompt_generic": compile_prompt_markdown([sh_timed], "generic", bible=bible).strip(),
            "prompt_runway": compile_prompt_markdown([sh_timed], "runway", bible=bible).strip(),
            "prompt_kling": compile_prompt_markdown([sh_timed], "kling", bible=bible).strip(),
        }
        if title:
            seg["work_title"] = title
        out.append(seg)
        t0 = t1
    return out


def segments_to_jsonl(segments: list[dict[str, Any]]) -> str:
    lines = []
    for s in segments:
        row = {k: v for k, v in s.items() if k not in ("prompt_generic", "prompt_runway", "prompt_kling")}
        row["prompts"] = {
            "generic": s.get("prompt_generic", ""),
            "runway": s.get("prompt_runway", ""),
            "kling": s.get("prompt_kling", ""),
        }
        lines.append(json.dumps(row, ensure_ascii=False))
    return "\n".join(lines)
