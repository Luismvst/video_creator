"""CLI de render por segmento (VideoZero v2 · Fase 3).

Por defecto en DRY-RUN: calcula coste, valida prompts y muestra el plan SIN gastar
ni necesitar FAL_KEY. Añade --no-dry-run (+ FAL_KEY en entorno) para generar de verdad.

Ejemplos (desde `backend`):
  # Estimación + plan sin gastar (segmentos = salida de music_planner.plan_timeline)
  python -m app.render_clip --segments segs.json --provider kling --max-budget 40

  # Probar solo el primer clip de verdad (gate de coste) con la key puesta:
  FAL_KEY=... python -m app.render_clip --segments segs.json --no-dry-run --limit 1

`segs.json`: array JSON de segmentos (cada uno con duration_sec y prompt_*).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from .render_client import DEFAULT_PROVIDER, DEFAULT_REROLL, PROVIDERS, render_timeline


def _load_segments(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    if not isinstance(data, list):
        raise ValueError("El JSON de segmentos debe ser una lista (o {'segments': [...]}).")
    return data


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="VideoZero v2-F3: render por segmento (dry-run por defecto).")
    parser.add_argument("--segments", required=True, help="JSON con la lista de segmentos del planner.")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=list(PROVIDERS), help="Motor de vídeo.")
    parser.add_argument("--reroll", type=float, default=DEFAULT_REROLL, help="Factor de rerolls para la estimación.")
    parser.add_argument("--max-budget", type=float, default=None, help="Tope USD; aborta si el estimado lo supera.")
    parser.add_argument("--limit", type=int, default=None, help="Renderizar solo los primeros N segmentos.")
    parser.add_argument("--out-dir", default="render_out", help="Carpeta de salida de clips.")
    parser.add_argument("--aspect", default="16:9", help="Relación de aspecto.")
    parser.add_argument("--no-dry-run", action="store_true", help="Generar de verdad (requiere FAL_KEY).")
    parser.add_argument("-o", "--output", default="", help="Guardar el manifiesto JSON en esta ruta.")
    args = parser.parse_args(argv)

    try:
        segments = _load_segments(args.segments)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"No pude leer segmentos: {e}", file=sys.stderr)
        return 1
    if not segments:
        print("La lista de segmentos está vacía.", file=sys.stderr)
        return 1

    result = render_timeline(
        segments,
        provider=args.provider,
        reroll_factor=args.reroll,
        max_budget_usd=args.max_budget,
        dry_run=not args.no_dry_run,
        out_dir=args.out_dir,
        aspect_ratio=args.aspect,
        limit=args.limit,
    )

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    est = result.get("estimate", {})
    print("\n--- Estimación de coste ---")
    if est:
        print(f"  Proveedor: {est['provider']} @ ${est['usd_per_sec']}/s × rerolls {est['reroll_factor']}")
        print(f"  {est['n_segments']} segmentos · {est['total_video_sec']}s de vídeo")
        print(f"  Subtotal: ${est['subtotal_usd']}  ->  Estimado con rerolls: ${est['estimated_usd']}")

    if result.get("aborted"):
        print(f"\n(!) ABORTADO antes de gastar: {result['reason']}", file=sys.stderr)
        return 2
    if not result.get("ok"):
        print(f"\nError: {result.get('error')}", file=sys.stderr)
        return 1

    mode = "DRY-RUN (no se generó nada)" if result["dry_run"] else f"render real → {result['out_dir']}"
    print(f"\nModo: {mode}")
    print(f"Segmentos OK: {result['rendered_ok']}/{len(result['segments'])}")
    if result.get("failed"):
        print(f"Fallidos: {len(result['failed'])} (ver manifiesto con -o)")
    if result["dry_run"]:
        print("\nPara generar de verdad: --no-dry-run con FAL_KEY en el entorno. "
              "Sugerencia: prueba primero --limit 1 (un clip) para validar coste/calidad.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
