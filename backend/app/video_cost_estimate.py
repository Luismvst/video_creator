"""Estimación orientativa de coste de generación de vídeo por proveedor (USD)."""

from __future__ import annotations

import os
from typing import Any


def _f(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# Valores por defecto: placeholders conservadores; el usuario puede sobreescribir con env.
DEFAULT_USD_PER_VIDEO_SECOND = {
    "generic": _f("VIDEOZERO_EST_USD_PER_SEC_GENERIC", 0.12),
    "runway": _f("VIDEOZERO_EST_USD_PER_SEC_RUNWAY", 0.15),
    "kling": _f("VIDEOZERO_EST_USD_PER_SEC_KLING", 0.10),
}


def estimate_segment_costs_usd(
    segments: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Suma coste por proveedor = duración × tarifa por segundo (lineal, orientativo).
    """
    totals: dict[str, float] = {k: 0.0 for k in DEFAULT_USD_PER_VIDEO_SECOND}
    per_seg: list[dict[str, Any]] = []
    for s in segments:
        dur = float(s.get("duration_sec") or 0)
        row = {"index": s.get("index"), "duration_sec": dur, "by_provider": {}}
        for prov, rate in DEFAULT_USD_PER_VIDEO_SECOND.items():
            est = round(dur * rate, 2)
            row["by_provider"][prov] = est
            totals[prov] += est
        per_seg.append(row)
    return {
        "totals_usd": {k: round(v, 2) for k, v in totals.items()},
        "per_segment": per_seg,
        "rates_usd_per_sec": dict(DEFAULT_USD_PER_VIDEO_SECOND),
        "disclaimer": "Estimación indicativa; las tarifas reales dependen del proveedor, resolución y plan.",
    }
