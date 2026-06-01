"""
Sesión guiada por consola: letra → preguntas de dirección → paquete creativo
→ segmentos con tiempos y promptings → estimación de coste (orientativa).

Ejecutar desde la carpeta `backend`:
  python -m app.cli_session
  python -m app.cli_session ruta/al/archivo_letra.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Optional

from .onboarding_ai import build_onboarding_package
from .timed_segments import propose_timed_segments
from .video_cost_estimate import estimate_segment_costs_usd
from .visual_bible import bible_to_markdown, build_visual_bible


def _read_multiline_lyrics() -> str:
    print(
        "\nPega la letra. Termina con una línea que contenga solo "
        "tres puntos (...) o una línea vacía seguida de Enter.\n",
    )
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "...":
            break
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _input_nonempty(prompt: str, default: Optional[str] = None) -> str:
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError:
            raw = ""
        if raw:
            return raw
        if default is not None:
            return default
        print("(Necesito una respuesta o un valor por defecto visible.)")


def _input_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        print(f"Valor no numérico, uso {default}.")
        return default


def _run_questionnaire() -> dict[str, str]:
    """Preguntas fijas estilo director; respuestas en texto libre."""
    print("\n--- Dirección (responde con frases cortas o largas, como prefieras) ---\n")
    out: dict[str, str] = {}
    pairs: list[tuple[str, str, Optional[str]]] = [
        (
            "mood",
            "¿Qué sensación global debe tener el vídeo al terminar de verlo?",
            None,
        ),
        (
            "space",
            "¿En qué espacios o lugares imaginás la acción (interior, calle, abstracto, mixto)?",
            None,
        ),
        (
            "protagonist",
            "¿Hay protagonista claro, grupo, o preferís algo más simbólico/anónimo?",
            None,
        ),
        (
            "visual_pace",
            "Ritmo visual: ¿más pausado y contemplativo, medio, o muy cortante y rápido?",
            None,
        ),
        (
            "light_color",
            "Luz y color: ¿qué paleta o contraste te imaginas (sin citar obras protegidas)?",
            None,
        ),
        (
            "avoid",
            "¿Qué deberíamos evitar a toda costa en imágenes o tono?",
            None,
        ),
        (
            "ending",
            "¿Cierre más abierto (eco emocional) o más resuelto (imagen final clara)?",
            None,
        ),
        (
            "refs",
            "Referencias libres (atmósfera, materiales, clima). Evitá nombres de artistas u obras concretas si podés.",
            None,
        ),
    ]
    for key, question, _d in pairs:
        print(question)
        out[key] = _input_nonempty("> ")
        print()
    return out


def _answers_to_brief(answers: dict[str, str]) -> str:
    parts = [
        f"Sensación deseada: {answers['mood']}",
        f"Espacios: {answers['space']}",
        f"Protagonista / presencia: {answers['protagonist']}",
        f"Ritmo visual: {answers['visual_pace']}",
        f"Luz y color: {answers['light_color']}",
        f"Evitar: {answers['avoid']}",
        f"Cierre: {answers['ending']}",
        f"Referencias de atmósfera: {answers['refs']}",
    ]
    return "\n".join(parts)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="VideoZero: sesion CMD de direccion y promptings.",
    )
    parser.add_argument(
        "lyrics_file",
        nargs="?",
        help="Archivo UTF-8 con la letra; si se omite, se pega en consola.",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Solo heurística local (sin OpenAI aunque haya API key).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="Guardar informe Markdown en esta ruta (opcional).",
    )
    args = parser.parse_args(argv)

    # Consola Windows: evitar UnicodeEncodeError con acentos/flechas (cp1252).
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass

    print(
        "\nVideoZero — modo consola\n"
        "Flujo: letra → preguntas de dirección → propuesta automática de tiempos por plano "
        "→ promptings (genérico / Runway / Kling) → estimación de coste orientativa.\n",
    )

    if args.lyrics_file:
        path = Path(args.lyrics_file)
        if not path.is_file():
            print(f"No existe el archivo: {path}", file=sys.stderr)
            return 1
        lyrics = path.read_text(encoding="utf-8").strip()
    else:
        lyrics = _read_multiline_lyrics()

    if not lyrics.strip():
        print("La letra está vacía. Saliendo.", file=sys.stderr)
        return 1

    title = input("\nTítulo de trabajo (opcional, Enter para omitir): ").strip() or None
    print("\nDuración total de la canción (segundos). El modelo repartirá planos sobre este tiempo.")
    total_sec = _input_float("Segundos", 180.0)

    answers = _run_questionnaire()
    brief = _answers_to_brief(answers)
    prefer_llm = not args.no_llm

    print("\n--- Generando dirección y planos (puede tardar si hay IA) ---\n")
    pkg, hint = build_onboarding_package(
        lyrics,
        brief,
        title=title,
        mood=answers.get("mood"),
        language="es",
        prefer_llm=prefer_llm,
    )
    shots = json.loads(pkg["shots_json"])
    if not isinstance(shots, list):
        shots = []

    # DIRQ-01: biblia visual estructurada, inyectada en cada prompt por capas.
    try:
        intake = json.loads(pkg.get("creative_intake_json") or "{}")
        style_attrs = intake.get("style_attributes") or []
    except json.JSONDecodeError:
        style_attrs = []
    bible = build_visual_bible(
        brief=brief,
        lyrics=lyrics,
        director_answers=answers,
        style_attributes=style_attrs,
        mood=answers.get("mood"),
    )

    segments = propose_timed_segments(total_sec, shots, title=title, bible=bible)
    costs = estimate_segment_costs_usd(segments)

    report_lines: list[str] = [
        "# VideoZero — sesión consola",
        "",
        f"*{hint}*",
        "",
        "## Nota sobre tiempos",
        "",
        "Las duraciones por plano son **propuesta heurística** repartida sobre la duración total "
        "que indicaste; podés ajustarlas a mano en post o pedir en otra herramienta que se "
        "recorten/estiren segmentos manteniendo la suma igual a la duración del tema.",
        "",
        "## Brief compuesto (dirección)",
        "",
        "```text",
        brief,
        "```",
        "",
        bible_to_markdown(bible).replace("# Biblia visual", "## Biblia visual"),
        "",
        "## Director (JSON)",
        "",
        "```json",
        pkg["director_answers_json"],
        "```",
        "",
        "## Intake creativo (JSON)",
        "",
        "```json",
        pkg["creative_intake_json"],
        "```",
        "",
        "## Planos con tiempo en la canción y promptings",
        "",
    ]

    for seg in segments:
        idx = seg["index"]
        report_lines.extend(
            [
                f"### Plano {idx} — {seg['start_sec']}s → {seg['end_sec']}s "
                f"(duración {seg['duration_sec']}s)",
                "",
                "**Shot (estructura)**",
                "",
                "```json",
                json.dumps(seg["shot"], ensure_ascii=False, indent=2),
                "```",
                "",
                "**Prompt — genérico**",
                "",
                seg.get("prompt_generic", ""),
                "",
                "**Prompt — Runway (orientativo MVP)**",
                "",
                seg.get("prompt_runway", ""),
                "",
                "**Prompt — Kling (orientativo MVP)**",
                "",
                seg.get("prompt_kling", ""),
                "",
                "---",
                "",
            ]
        )

    report_lines.extend(
        [
            "## Estimación de coste (USD, orientativa)",
            "",
            f"* {costs['disclaimer']}",
            "",
            "Tarifas usadas (USD/s, configurables por variables de entorno `VIDEOZERO_EST_USD_PER_SEC_*`):",
            "",
            "```json",
            json.dumps(costs["rates_usd_per_sec"], indent=2),
            "```",
            "",
            "**Totales por proveedor (suma de todos los planos)**",
            "",
            "```json",
            json.dumps(costs["totals_usd"], indent=2),
            "```",
            "",
        ]
    )

    report = "\n".join(report_lines)
    print(report)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report, encoding="utf-8")
        print(f"\nInforme guardado en: {out_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
