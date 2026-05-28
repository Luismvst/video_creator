"""CLI único end-to-end (VideoZero v2): letra (+URL/audio) → videoclip_final.mp4.

Dry-run por defecto: calcula tiempos, timeline, costes y el plan de render+ensamblado
SIN gastar ni necesitar FAL_KEY/ffmpeg. Con --run ejecuta de verdad.

Ejemplos (desde `backend`):
  # Plan completo + coste, sin gastar (solo letra + duración objetivo)
  python -m app.make_video --lyrics letra.txt --duration 180 --provider kling --max-budget 40

  # Con canción real (YouTube) y subtítulos, todavía dry-run
  python -m app.make_video --lyrics letra.txt --url "https://youtu.be/XXXX" --keyframes

  # Producción real (requiere FAL_KEY en entorno + ffmpeg en PATH)
  FAL_KEY=... python -m app.make_video --lyrics letra.txt --url "..." --run --max-budget 40
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .pipeline import run_pipeline
from .render_client import DEFAULT_PROVIDER, DEFAULT_REROLL, PROVIDERS


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="VideoZero v2: pipeline E2E letra→MP4 (dry-run por defecto).")
    p.add_argument("--lyrics", required=True, help="Archivo .txt UTF-8 con la letra.")
    p.add_argument("--url", help="URL de YouTube del tema (contenido del que tengas derechos).")
    p.add_argument("--audio", help="Archivo de audio local (alternativa a --url).")
    p.add_argument("--brief", default="", help="Brief de dirección (texto libre).")
    p.add_argument("--title", help="Título de trabajo.")
    p.add_argument("--mood", help="Mood/sensación global.")
    p.add_argument("--lang", default="es", help="Idioma (def: es).")
    p.add_argument("--duration", type=float, help="Duración objetivo (s) si no hay audio.")
    p.add_argument("--provider", default=DEFAULT_PROVIDER, choices=list(PROVIDERS), help="Motor de vídeo.")
    p.add_argument("--reroll", type=float, default=DEFAULT_REROLL, help="Factor de rerolls para la estimación.")
    p.add_argument("--max-budget", type=float, default=None, help="Tope USD (aborta el render si lo supera).")
    p.add_argument("--keyframes", action="store_true", help="Planificar keyframes encadenados (F4).")
    p.add_argument("--no-subtitles", action="store_true", help="No quemar la letra como subtítulos.")
    p.add_argument("--llm", action="store_true", help="Usar OpenAI para los shots (requiere OPENAI_API_KEY).")
    p.add_argument("--no-stems", action="store_true", help="No separar voz con Demucs.")
    p.add_argument("--work-dir", default="vz_work", help="Carpeta de trabajo/artefactos.")
    p.add_argument("--out", default="videoclip_final.mp4", help="Ruta del MP4 final.")
    p.add_argument("--run", action="store_true", help="Ejecutar de verdad (requiere FAL_KEY + ffmpeg).")
    p.add_argument("-o", "--output", default="", help="Guardar el manifiesto JSON aquí.")
    args = p.parse_args(argv)

    lp = Path(args.lyrics)
    if not lp.is_file():
        print(f"No existe la letra: {lp}", file=sys.stderr)
        return 1
    lyrics = lp.read_text(encoding="utf-8").strip()
    if not lyrics:
        print("La letra está vacía.", file=sys.stderr)
        return 1
    if not args.url and not args.audio and not args.duration:
        print("Sin --url/--audio necesito --duration (modo solo-letra).", file=sys.stderr)
        return 1

    manifest = run_pipeline(
        lyrics_text=lyrics, url=args.url, audio_file=args.audio, brief=args.brief,
        title=args.title, mood=args.mood, language=args.lang, target_duration=args.duration,
        provider=args.provider, reroll_factor=args.reroll, max_budget_usd=args.max_budget,
        keyframes=args.keyframes, subtitles=not args.no_subtitles, prefer_llm=args.llm,
        do_stems=not args.no_stems, work_dir=args.work_dir, out_path=args.out,
        dry_run=not args.run,
    )

    if args.output:
        Path(args.output).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    c = manifest["cost"]
    print("\n=== VideoZero — manifiesto ===")
    print(f"  Modo: {'DRY-RUN (no gasta)' if manifest['dry_run'] else 'PRODUCCIÓN'}")
    print(f"  Shots: {manifest['n_shots']} ({manifest['shots_note']})")
    print(f"  Timeline: {manifest['n_segments']} segmentos · fuente {manifest['timeline_source']} · "
          f"{manifest['duration_sec']}s")
    if manifest["degraded_audio"]:
        print("  (audio degradado: faltan herramientas de F1 o no hay audio — revisa f1_ingest_steps)")
    print(f"  Coste estimado: render ${c['render_usd']}"
          + (f" + keyframes ${c['keyframes_usd']}" if c['keyframes_usd'] else "")
          + f"  =>  TOTAL ~${c['total_estimated_usd']}")
    if c["over_budget"]:
        print(f"  (!) Render ABORTADO: supera el tope ${c['max_budget_usd']}.", file=sys.stderr)
    a = manifest["f5_assembly"]
    print(f"  Ensamblado: clips={a['n_clips']} · ffmpeg={a['ffmpeg_available']} · "
          f"{'OK' if a['ok'] else 'bloqueado: ' + str(a.get('reason'))}")
    if manifest["artifacts"]:
        print(f"  Artefactos: {manifest['artifacts'].get('segments')}")
    if manifest["dry_run"]:
        print("\n  Dry-run: nada generado. Con FAL_KEY + ffmpeg, repite con --run "
              "(prueba antes 1 clip con app.render_clip --no-dry-run --limit 1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
