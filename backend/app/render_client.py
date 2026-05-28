"""Cliente de render de vídeo por segmento (VideoZero v2 · Fase 3).

Toma los segmentos del planner (`music_planner.plan_timeline`) y genera un clip por
segmento vía **fal.ai** (gateway a Kling 3.0 / Veo 3.1 / Wan, etc.).

Seguridad de coste (requisito del producto):
  1. `estimate_render_cost()` calcula el coste con tarifas 2026 + factor de rerolls.
  2. `within_budget()` compara con el tope `MAX_BUDGET_USD`.
  3. `render_timeline()` **aborta ANTES de gastar** si el estimado supera el tope.

Modo `dry_run=True` (por defecto): valida prompts y calcula coste, **no genera nada**
y **no necesita FAL_KEY**. Solo con `dry_run=False` + `FAL_KEY` se llama a la API real.

Sin dependencias pesadas: la llamada HTTP usa urllib (mismo estilo que `onboarding_ai`).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Configuración de proveedores (tarifas 2026; ver .planning/V2-RENDER-PIPELINE.md §5)
# --------------------------------------------------------------------------- #

def _f(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# USD por segundo de vídeo generado. Sobreescribible por entorno.
PROVIDERS: dict[str, dict[str, Any]] = {
    "kling": {  # default recomendado: mejor calidad/precio
        "usd_per_sec": _f("VIDEOZERO_USD_PER_SEC_KLING", 0.10),
        "fal_model": os.environ.get("VIDEOZERO_FAL_MODEL_KLING", "fal-ai/kling-video/v2/standard/text-to-video"),
        "prompt_field": "prompt_kling",
    },
    "veo3_fast": {
        "usd_per_sec": _f("VIDEOZERO_USD_PER_SEC_VEO3_FAST", 0.15),
        "fal_model": os.environ.get("VIDEOZERO_FAL_MODEL_VEO3_FAST", "fal-ai/veo3/fast"),
        "prompt_field": "prompt_generic",
    },
    "veo3": {  # premium 4K + audio
        "usd_per_sec": _f("VIDEOZERO_USD_PER_SEC_VEO3", 0.75),
        "fal_model": os.environ.get("VIDEOZERO_FAL_MODEL_VEO3", "fal-ai/veo3"),
        "prompt_field": "prompt_generic",
    },
    "wan": {  # económico
        "usd_per_sec": _f("VIDEOZERO_USD_PER_SEC_WAN", 0.05),
        "fal_model": os.environ.get("VIDEOZERO_FAL_MODEL_WAN", "fal-ai/wan/v2.6/text-to-video"),
        "prompt_field": "prompt_generic",
    },
    "runway": {
        "usd_per_sec": _f("VIDEOZERO_USD_PER_SEC_RUNWAY", 0.15),
        "fal_model": os.environ.get("VIDEOZERO_FAL_MODEL_RUNWAY", "fal-ai/runway-gen4/turbo"),
        "prompt_field": "prompt_runway",
    },
}

DEFAULT_PROVIDER = os.environ.get("VIDEOZERO_VIDEO_PROVIDER", "kling")
DEFAULT_REROLL = _f("VIDEOZERO_REROLL_FACTOR", 1.4)


def _provider_cfg(provider: str) -> dict[str, Any]:
    cfg = PROVIDERS.get(provider)
    if cfg is None:
        raise ValueError(f"Proveedor desconocido: {provider}. Opciones: {', '.join(PROVIDERS)}")
    return cfg


def provider_prompt(segment: dict[str, Any], provider: str) -> str:
    """Selecciona el prompt adecuado al proveedor, con fallback a genérico."""
    field = _provider_cfg(provider)["prompt_field"]
    return (segment.get(field) or segment.get("prompt_generic") or "").strip()


# --------------------------------------------------------------------------- #
# Estimación de coste y gate de presupuesto (PUROS)
# --------------------------------------------------------------------------- #

def estimate_render_cost(
    segments: list[dict[str, Any]],
    *,
    provider: str = DEFAULT_PROVIDER,
    reroll_factor: float = DEFAULT_REROLL,
) -> dict[str, Any]:
    """Coste total = Σ duración × tarifa/seg × factor_rerolls (lineal, orientativo)."""
    rate = float(_provider_cfg(provider)["usd_per_sec"])
    per_segment: list[dict[str, Any]] = []
    total_sec = 0.0
    for s in segments:
        dur = float(s.get("duration_sec") or 0.0)
        total_sec += dur
        per_segment.append(
            {"index": s.get("index"), "duration_sec": round(dur, 2), "usd": round(dur * rate, 4)}
        )
    subtotal = round(total_sec * rate, 2)
    estimated = round(subtotal * float(reroll_factor), 2)
    return {
        "provider": provider,
        "usd_per_sec": rate,
        "reroll_factor": float(reroll_factor),
        "n_segments": len(segments),
        "total_video_sec": round(total_sec, 2),
        "subtotal_usd": subtotal,
        "estimated_usd": estimated,
        "per_segment": per_segment,
        "disclaimer": "Estimación orientativa; la tarifa real depende de resolución, plan y nº de rerolls.",
    }


def within_budget(
    estimate: dict[str, Any], max_budget_usd: Optional[float]
) -> tuple[bool, Optional[str]]:
    """True si el estimado cabe en el tope. `max_budget_usd=None` → sin tope."""
    if max_budget_usd is None:
        return True, None
    est = float(estimate.get("estimated_usd", 0.0))
    if est > float(max_budget_usd):
        return False, (
            f"Estimado ${est:.2f} supera el tope ${float(max_budget_usd):.2f} "
            f"({estimate.get('n_segments')} segs, {estimate.get('total_video_sec')}s "
            f"@ ${estimate.get('usd_per_sec')}/s × {estimate.get('reroll_factor')})."
        )
    return True, None


# --------------------------------------------------------------------------- #
# Render por segmento
# --------------------------------------------------------------------------- #

def render_segment(
    segment: dict[str, Any],
    *,
    provider: str = DEFAULT_PROVIDER,
    dry_run: bool = True,
    fal_key: Optional[str] = None,
    out_dir: str = "render_out",
    aspect_ratio: str = "16:9",
    timeout_sec: float = 600.0,
) -> dict[str, Any]:
    """Genera (o planifica, en dry-run) el clip de un segmento."""
    cfg = _provider_cfg(provider)
    prompt = provider_prompt(segment, provider)
    idx = segment.get("index")
    dur = float(segment.get("duration_sec") or 0.0)
    clip_name = f"clip_{int(idx):03d}.mp4" if isinstance(idx, int) else "clip.mp4"

    if not prompt:
        return {"ok": False, "index": idx, "error": "Segmento sin prompt utilizable."}

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "index": idx,
            "provider": provider,
            "model": cfg["fal_model"],
            "duration_sec": round(dur, 2),
            "aspect_ratio": aspect_ratio,
            "prompt_preview": prompt[:240],
            "would_write": str(Path(out_dir) / clip_name),
        }

    key = fal_key or os.environ.get("FAL_KEY")
    if not key:
        return {"ok": False, "index": idx, "error": "Falta FAL_KEY (o usa dry_run=True)."}

    return _fal_generate(
        cfg["fal_model"], prompt, dur, key,
        out_path=Path(out_dir) / clip_name, aspect_ratio=aspect_ratio, timeout_sec=timeout_sec,
    )


def render_timeline(
    segments: list[dict[str, Any]],
    *,
    provider: str = DEFAULT_PROVIDER,
    reroll_factor: float = DEFAULT_REROLL,
    max_budget_usd: Optional[float] = None,
    dry_run: bool = True,
    fal_key: Optional[str] = None,
    out_dir: str = "render_out",
    aspect_ratio: str = "16:9",
    limit: Optional[int] = None,
) -> dict[str, Any]:
    """Estima coste → comprueba presupuesto (aborta antes de gastar) → renderiza.

    `limit`: renderiza solo los primeros N segmentos (útil para el gate de coste:
    probar 1 clip antes de lanzar la canción entera).
    """
    if not segments:
        return {"ok": False, "error": "Sin segmentos. Genera el timeline con music_planner."}

    to_render = segments[:limit] if limit else segments
    estimate = estimate_render_cost(to_render, provider=provider, reroll_factor=reroll_factor)

    ok, reason = within_budget(estimate, max_budget_usd)
    if not ok:
        return {"ok": False, "aborted": True, "reason": reason, "estimate": estimate}

    if not dry_run and not (fal_key or os.environ.get("FAL_KEY")):
        return {"ok": False, "error": "Falta FAL_KEY para render real (o usa dry_run=True).",
                "estimate": estimate}

    if not dry_run:
        Path(out_dir).mkdir(parents=True, exist_ok=True)

    results = [
        render_segment(
            s, provider=provider, dry_run=dry_run, fal_key=fal_key,
            out_dir=out_dir, aspect_ratio=aspect_ratio,
        )
        for s in to_render
    ]
    return {
        "ok": True,
        "dry_run": dry_run,
        "provider": provider,
        "estimate": estimate,
        "rendered_ok": sum(1 for r in results if r.get("ok")),
        "failed": [r for r in results if not r.get("ok")],
        "segments": results,
        "out_dir": out_dir,
    }


# --------------------------------------------------------------------------- #
# Llamada real a fal.ai (queue API)
# --------------------------------------------------------------------------- #

def _http_json(url: str, *, method: str = "GET", key: str,
               body: Optional[dict[str, Any]] = None, timeout: float = 60.0) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fal_generate(
    model: str, prompt: str, duration_sec: float, key: str,
    *, out_path: Path, aspect_ratio: str, timeout_sec: float,
) -> dict[str, Any]:
    """Envía el trabajo a la cola de fal.ai, hace polling y descarga el MP4.

    Nota: el esquema exacto de input/endpoints de fal evoluciona; modelo y campos
    son configurables por entorno. Por eso el camino real está aislado y el dry-run
    es el modo por defecto.
    """
    submit_url = f"https://queue.fal.run/{model}"
    payload = {
        "prompt": prompt,
        "duration": int(round(duration_sec)) or 5,
        "aspect_ratio": aspect_ratio,
    }
    try:
        submitted = _http_json(submit_url, method="POST", key=key, body=payload, timeout=60.0)
        status_url = submitted.get("status_url") or submitted.get("response_url")
        if not status_url:
            return {"ok": False, "error": f"Respuesta fal sin status_url: {submitted}"}

        deadline = time.monotonic() + timeout_sec
        result: dict[str, Any] = {}
        while time.monotonic() < deadline:
            st = _http_json(status_url, key=key, timeout=60.0)
            state = st.get("status")
            if state == "COMPLETED":
                result = _http_json(submitted.get("response_url", status_url), key=key, timeout=60.0)
                break
            if state in ("FAILED", "ERROR"):
                return {"ok": False, "error": f"fal estado {state}: {st}"}
            time.sleep(3.0)
        else:
            return {"ok": False, "error": "Timeout esperando a fal.ai."}

        video_url = (result.get("video") or {}).get("url") or result.get("url")
        if not video_url:
            return {"ok": False, "error": f"Resultado fal sin URL de vídeo: {result}"}

        out_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(video_url, str(out_path))
        return {"ok": True, "dry_run": False, "video_url": video_url, "path": str(out_path)}
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:400]
        except OSError:
            detail = str(e)
        return {"ok": False, "error": f"fal HTTP {e.code}: {detail}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"fal: {e}"}
