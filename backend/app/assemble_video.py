"""CLI de ensamblado final (VideoZero v2 · Fase 5).

Concatena los clips generados + pega el audio original → videoclip_final.mp4.
Dry-run por defecto (muestra el plan/comando ffmpeg sin ejecutar).

Ejemplos (desde `backend`):
  # Plan sin ejecutar (comprueba clips/audio/ffmpeg)
  python -m app.assemble_video --segments segs.json --clips-dir render_out \
      --audio song.wav --out videoclip_final.mp4

  # Ensamblar de verdad, con subtítulos de la letra (requiere ffmpeg en PATH)
  python -m app.assemble_video --segments segs.json --clips-dir render_out \
      --audio song.wav --timings timings.json --subtitles --out final.mp4 --run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from .video_assembly import assemble


def _load_list(path: Optional[str], key: Optional[str] = None) -> Optional[list[dict[str, Any]]]:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if key and key in data:
            data = data[key]
        elif "segments" in data:
            data = data["segments"]
        elif "line_timings" in data:
            data = data["line_timings"]
    return data if isinstance(data, list) else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="VideoZero v2-F5: ensamblar clips + audio → MP4 final.")
    parser.add_argument("--segments", help="JSON de segmentos (deriva clip_NNN.mp4 en --clips-dir).")
    parser.add_argument("--clips-dir", help="Carpeta con los clips generados.")
    parser.add_argument("--audio", required=True, help="Audio original de la canción (wav/mp3).")
    parser.add_argument("--out", default="videoclip_final.mp4", help="Ruta del MP4 final.")
    parser.add_argument("--timings", help="JSON con line_timings (para subtítulos).")
    parser.add_argument("--subtitles", action="store_true", help="Quemar la letra como subtítulos.")
    parser.add_argument("--run", action="store_true", help="Ejecutar ffmpeg de verdad (def: dry-run).")
    parser.add_argument("-o", "--output", default="", help="Guardar el plan/manifiesto JSON aquí.")
    args = parser.parse_args(argv)

    try:
        segments = _load_list(args.segments)
        timings = _load_list(args.timings, key="line_timings")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"No pude leer los JSON: {e}", file=sys.stderr)
        return 1

    result = assemble(
        out_path=args.out,
        audio_path=args.audio,
        clips_dir=args.clips_dir,
        segments=segments,
        line_timings=timings,
        subtitles=args.subtitles,
        dry_run=not args.run,
    )

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n--- Plan de ensamblado ---")
    print(f"  Clips: {result.get('n_clips')}  ·  audio presente: {result.get('audio_present')}  "
          f"·  ffmpeg: {result.get('ffmpeg_available')}  ·  subtítulos: {result.get('subtitles')}")
    if result.get("missing_clips"):
        print(f"  Faltan {len(result['missing_clips'])} clip(s).")
    print("\n  Comando ffmpeg:")
    print("    " + " ".join(result.get("command", [])))

    if not result.get("ok"):
        print(f"\n(!) No se puede ensamblar todavía: {result.get('reason') or result.get('error')}",
              file=sys.stderr)
        return 2
    if result.get("dry_run"):
        print("\nDry-run: no se ejecutó nada. Añade --run (con ffmpeg en PATH) para crear el MP4.")
    else:
        print(f"\nListo: {result.get('out_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
