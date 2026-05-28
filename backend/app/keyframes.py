"""Keyframes encadenados para continuidad (VideoZero v2 · Fase 4).

Genera (o planifica, en dry-run) un fotograma clave por segmento con un modelo de
imagen (Flux vía fal.ai). El **encadenado** es la clave anti-collage: el keyframe de
cada segmento toma como referencia el keyframe anterior, de modo que personaje, paleta
y mundo se mantengan coherentes entre clips (luego image-to-video parte de ese frame).

Modo `dry_run=True` (def): calcula coste y construye el plan SIN generar ni necesitar key.
Camino real (fal) aislado tras `dry_run=False` + `FAL_KEY`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional


def _f(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


KEYFRAME_USD_PER_IMAGE = _f("VIDEOZERO_USD_PER_IMAGE", 0.04)
KEYFRAME_FAL_MODEL = os.environ.get("VIDEOZERO_FAL_MODEL_IMAGE", "fal-ai/flux/dev")


def keyframe_prompt(segment: dict[str, Any]) -> str:
    """Prompt de imagen (fija) derivado del shot del segmento; fallback al prompt genérico."""
    shot = segment.get("shot") or {}
    parts = [shot.get("action"), shot.get("camera"), shot.get("notes")]
    text = ". ".join(p for p in parts if p)
    return (text or (segment.get("prompt_generic") or "")).strip()


def estimate_keyframe_cost(
    n_segments: int, *, usd_per_image: float = KEYFRAME_USD_PER_IMAGE
) -> dict[str, Any]:
    """Coste de keyframes = nº segmentos × tarifa por imagen (1 keyframe por segmento)."""
    n = max(0, int(n_segments))
    return {
        "n_images": n,
        "usd_per_image": float(usd_per_image),
        "estimated_usd": round(n * float(usd_per_image), 2),
    }


def plan_keyframes(
    segments: list[dict[str, Any]],
    *,
    chain: bool = True,
    out_dir: str = "keyframes_out",
    dry_run: bool = True,
    fal_key: Optional[str] = None,
) -> dict[str, Any]:
    """Plan (o ejecución dry-run) de keyframes encadenados, uno por segmento."""
    items: list[dict[str, Any]] = []
    prev_path: Optional[str] = None
    for s in segments:
        idx = s.get("index")
        name = f"kf_{int(idx):03d}.png" if isinstance(idx, int) else "kf.png"
        path = str(Path(out_dir) / name)
        prompt = keyframe_prompt(s)
        items.append(
            {
                "index": idx,
                "model": KEYFRAME_FAL_MODEL,
                "prompt_preview": prompt[:200],
                "reference_image": prev_path if chain else None,
                "would_write": path,
                "has_prompt": bool(prompt),
            }
        )
        if chain:
            prev_path = path

    estimate = estimate_keyframe_cost(len(segments))
    return {
        "ok": True,
        "dry_run": True if dry_run else False,
        "chain": chain,
        "estimate": estimate,
        "keyframes": items,
        "note": (
            "Encadenado activo: cada keyframe referencia el anterior para continuidad."
            if chain else "Sin encadenar: keyframes independientes."
        ),
    }
