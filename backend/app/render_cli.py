"""
CLI de render: de un `segments.json` a clips de vídeo (o plan en dry-run).

Por defecto **dry-run** (no gasta, no necesita FAL_KEY): estima coste, valida
modelo/segmentos y comprueba el gate de presupuesto. Con `--run` + `FAL_KEY`
llama a fal.ai de verdad.

Ejemplos (desde la carpeta `backend`):
  python -m app.render_cli --segments ../letras/filomena_segments.json
  python -m app.render_cli --segments ../letras/filomena_segments.json --provider veo3_fast
  python -m app.render_cli --segments ../letras/filomena_segments.json --limit 1 --run

El `segments.json` es una lista de segmentos con los campos que produce
`timed_segments.propose_timed_segments` / `music_planner.plan_timeline`
(index, duration_sec, prompt_generic/prompt_runway/prompt_kling, …).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from .render_client import DEFAULT_PROVIDER, PROVIDERS, render_timeline


def _reconfigure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def _load_segments(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("segments"), list):
        data = data["segments"]
    if not isinstance(data, list):
        raise ValueError("El JSON debe ser una lista de segmentos o {'segments': [...]}.")
    return data


def main(argv: Optional[list[str]] = None) -> int:
    _reconfigure_utf8()
    parser = argparse.ArgumentParser(description="VideoZero: render de timeline (dry-run por defecto).")
    parser.add_argument("--segments", required=True, help="Ruta al segments.json.")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=list(PROVIDERS),
                        help=f"Motor de vídeo (def: {DEFAULT_PROVIDER}).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Renderiza solo los primeros N segmentos (prueba 1 clip antes de la canción entera).")
    parser.add_argument("--max-budget", type=float, default=None,
                        help="Tope USD; aborta antes de gastar si el estimado lo supera.")
    parser.add_argument("--out-dir", default="render_out", help="Carpeta de salida de los clips.")
    parser.add_argument("--aspect", default="16:9", help="Aspect ratio (def: 16:9).")
    parser.add_argument("--run", action="store_true",
                        help="Render REAL (gasta; requiere FAL_KEY). Sin este flag = dry-run.")
    args = parser.parse_args(argv)

    seg_path = Path(args.segments)
    if not seg_path.is_file():
        print(f"No existe el archivo de segmentos: {seg_path}", file=sys.stderr)
        return 1
    try:
        segments = _load_segments(seg_path)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"segments.json inválido: {e}", file=sys.stderr)
        return 1

    result = render_timeline(
        segments,
        provider=args.provider,
        max_budget_usd=args.max_budget,
        dry_run=not args.run,
        out_dir=args.out_dir,
        aspect_ratio=args.aspect,
        limit=args.limit,
    )

    est = result.get("estimate", {})
    mode = "DRY-RUN (sin gasto)" if not args.run else "RENDER REAL"
    print(f"\nVideoZero render — {mode} · proveedor {args.provider}")
    if est:
        print(
            f"  segmentos: {est.get('n_segments')} · vídeo {est.get('total_video_sec')}s · "
            f"subtotal ${est.get('subtotal_usd')} · estimado(x{est.get('reroll_factor')}) "
            f"${est.get('estimated_usd')}"
        )
    if not result.get("ok"):
        print(f"  ABORTADO: {result.get('reason') or result.get('error')}", file=sys.stderr)
        return 2
    if not args.run:
        print(f"  OK: se generarían {len(result.get('segments', []))} clips en '{args.out_dir}' "
              "(usa --run + FAL_KEY para generar de verdad).")
    else:
        print(f"  OK: {result.get('rendered_ok')} clips generados en '{args.out_dir}'. "
              f"Fallidos: {len(result.get('failed', []))}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
