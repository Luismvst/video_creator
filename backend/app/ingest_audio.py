"""CLI de ingesta de audio + alineación letra↔tiempo (VideoZero v2 · Fase 1).

Ejemplos (desde la carpeta `backend`):
  python -m app.ingest_audio --url "https://youtu.be/XXXX" --lyrics letra.txt -o timings.json
  python -m app.ingest_audio --audio song.wav --lyrics letra.txt --no-stems -o timings.json
  python -m app.ingest_audio --check            # solo comprueba qué herramientas hay

Salida: JSON con line_timings (línea→start/end), análisis musical (BPM/beats/energía)
y el detalle de qué pasos corrieron o se degradaron. Todo local, sin APIs de pago.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .audio_ingest import check_tools, ingest_and_align


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="VideoZero v2-F1: audio → tiempos de letra + análisis musical (local).",
    )
    parser.add_argument("--url", help="URL de YouTube del tema (contenido del que tengas derechos).")
    parser.add_argument("--audio", help="Archivo de audio local (alternativa a --url).")
    parser.add_argument("--lyrics", help="Archivo .txt UTF-8 con la letra (fuente de verdad).")
    parser.add_argument("--lang", default="es", help="Idioma para la alineación (def: es).")
    parser.add_argument("--no-stems", action="store_true", help="No separar voz con Demucs.")
    parser.add_argument("--work-dir", default="audio_work", help="Carpeta de trabajo.")
    parser.add_argument("-o", "--output", default="", help="Guardar JSON en esta ruta.")
    parser.add_argument("--check", action="store_true", help="Solo comprobar herramientas y salir.")
    args = parser.parse_args(argv)

    if args.check:
        tools = check_tools()
        print(json.dumps({"tools": tools}, indent=2, ensure_ascii=False))
        missing = [k for k, v in tools.items() if not v]
        if missing:
            print(f"\nFaltan: {', '.join(missing)} — pip install -r requirements-audio.txt "
                  f"(+ yt-dlp y ffmpeg en PATH).", file=sys.stderr)
        return 0

    if not args.lyrics:
        print("Falta --lyrics (la letra es obligatoria).", file=sys.stderr)
        return 1
    lyrics_path = Path(args.lyrics)
    if not lyrics_path.is_file():
        print(f"No existe el archivo de letra: {lyrics_path}", file=sys.stderr)
        return 1
    lyrics = lyrics_path.read_text(encoding="utf-8").strip()
    if not lyrics:
        print("La letra está vacía.", file=sys.stderr)
        return 1

    if not args.url and not args.audio:
        print("Necesito --url o --audio (o usa el flujo solo-letra en app.cli_session).",
              file=sys.stderr)
        return 1

    result = ingest_and_align(
        lyrics_text=lyrics,
        url=args.url,
        audio_file=args.audio,
        work_dir=args.work_dir,
        language=args.lang,
        do_stems=not args.no_stems,
    )

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
        print(f"Guardado en: {Path(args.output).resolve()}")

    # Resumen legible por consola
    print("\n--- Resumen ingesta ---")
    for s in result["steps"]:
        mark = "ok" if s.get("ok") else "··"
        extra = s.get("error") or s.get("note") or ""
        print(f"  [{mark}] {s['step']}: {extra}")
    lt = result.get("line_timings") or []
    timed = [r for r in lt if r.get("start") is not None]
    print(f"\nLíneas con tiempo: {len(timed)}/{len(lt)}")
    music = result.get("music") or {}
    if music.get("available"):
        print(f"BPM: {music.get('bpm')} · duración: {music.get('duration_sec')}s · "
              f"beats: {len(music.get('beats', []))} · secciones: {len(music.get('sections', []))}")
    if result.get("degraded"):
        print("\n(!) Modo degradado: algún paso no estuvo disponible. Revisa --check.")
    if not args.output:
        print("\n(JSON completo: añade -o salida.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
