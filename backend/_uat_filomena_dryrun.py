"""Dry-run de render para 'Filomena' (sin gastar, sin FAL_KEY).

Estima coste real por proveedor (tarifas 2026 + factor de rerolls), valida el
modelo fal y los segmentos, y comprueba el gate de presupuesto. NO llama a fal.ai.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import _uat_filomena as fil  # reutiliza biblia + planos + segmentos de la sesión
from app.render_client import PROVIDERS, estimate_render_cost, render_timeline

for _s in (sys.stdout, sys.stderr):
    _r = getattr(_s, "reconfigure", None)
    if callable(_r):
        try:
            _r(encoding="utf-8")
        except (ValueError, OSError):
            pass

segments = fil.segments
OUT = Path(__file__).resolve().parent.parent / "letras" / "filomena_render_dryrun.md"

# Tope de presupuesto de ejemplo (configurable). Aborta antes de gastar si se supera.
MAX_BUDGET_USD = 25.0
PROVIDERS_TO_CHECK = ["kling", "veo3_fast", "veo3", "runway", "wan"]

R: list[str] = [
    "# VideoZero — dry-run de render: Filomena",
    "",
    f"*Sin gasto · sin FAL_KEY · {len(segments)} segmentos · tope ${MAX_BUDGET_USD:.0f} · factor rerolls 1.4.*",
    "",
    "## Coste estimado por proveedor (incluye factor de rerolls)",
    "",
    "| Proveedor | Modelo fal | $/s | Vídeo (s) | Subtotal | Estimado* | ¿Cabe en tope? |",
    "|---|---|---|---|---|---|---|",
]

first_provider_segments_dump = None
for prov in PROVIDERS_TO_CHECK:
    est = estimate_render_cost(segments, provider=prov)
    res = render_timeline(segments, provider=prov, max_budget_usd=MAX_BUDGET_USD, dry_run=True)
    fits = "✅" if res.get("ok") else f"❌ {res.get('reason', '')[:40]}"
    R.append(
        f"| {prov} | `{PROVIDERS[prov]['fal_model']}` | {est['usd_per_sec']} | "
        f"{est['total_video_sec']} | ${est['subtotal_usd']} | **${est['estimated_usd']}** | {fits} |"
    )
    if prov == "kling" and res.get("ok"):
        first_provider_segments_dump = res["segments"]

R += [
    "",
    "*\\* Estimado = subtotal × 1.4 (reserva para rerolls). El subtotal es el coste de una sola pasada.*",
    "",
    "## Plan de render por segmento (Kling, dry-run — lo que se generaría)",
    "",
]
for seg in first_provider_segments_dump or []:
    R += [
        f"### Clip {seg['index']:03d} — {seg['duration_sec']}s · {seg['aspect_ratio']}",
        f"- **Modelo:** `{seg['model']}`",
        f"- **Salida:** `{seg['would_write']}`",
        f"- **Prompt (preview):** {seg['prompt_preview']}",
        "",
    ]

R += [
    "## Cómo lanzar el render real (cuando quieras gastar)",
    "",
    "```powershell",
    "cd backend",
    "# 1) genera segments.json desde la sesión guiada (ya hecho para Filomena)",
    "python _uat_filomena.py",
    "# 2) dry-run del render (sin gastar): valida modelo, coste y gate",
    "python -m app.render_cli --segments ../letras/filomena_segments.json --provider kling --max-budget 25",
    "# 3) render REAL — primero 1 clip para validar calidad antes de la canción entera",
    "$env:FAL_KEY = \"<tu_clave_fal>\"",
    "python -m app.render_cli --segments ../letras/filomena_segments.json --provider kling --limit 1 --run",
    "```",
    "",
    "> El gate aborta automáticamente si el estimado supera `--max-budget`. Empieza con `--limit 1`.",
]

report = "\n".join(R)
OUT.write_text(report, encoding="utf-8")
# Resumen compacto a stdout
print(f"[dry-run ok] {len(segments)} segmentos · informe en {OUT}")
for prov in PROVIDERS_TO_CHECK:
    est = estimate_render_cost(segments, provider=prov)
    print(f"  {prov:10s} subtotal ${est['subtotal_usd']:6.2f}  estimado(x1.4) ${est['estimated_usd']:6.2f}")
