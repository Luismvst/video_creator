"""Sesión guiada (Claude como director IA) para 'Filomena' con prompting de dirección F6.

Genera la dirección + biblia visual + planos con tiempos + prompts por capas
(genérico/Veo, Runway, Kling) + estimación de coste. Throwaway UAT/regen script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.prompt_compile import compile_segment_prompt
from app.timed_segments import propose_timed_segments
from app.video_cost_estimate import estimate_segment_costs_usd
from app.visual_bible import bible_to_markdown, build_visual_bible

for _s in (sys.stdout, sys.stderr):
    _r = getattr(_s, "reconfigure", None)
    if callable(_r):
        try:
            _r(encoding="utf-8")
        except (ValueError, OSError):
            pass

TITLE = "Filomena"
TOTAL_SEC = 120.0

ROOT = Path(__file__).resolve().parent.parent
LYRICS_PATH = ROOT / "letras" / "filomena_bucero.txt"
OUT_PATH = ROOT / "letras" / "filomena_session.md"

# --- Dirección capturada en la entrevista guiada (respuestas del usuario) ---
director_answers = {
    "mood": "Melancolía que vira a esperanza",
    "space": "Calle nevada, exterior urbano, ciudad paralizada",
    "protagonist": "Simbólico / sin rostro; la nieve y la ciudad son protagonistas",
    "visual_pace": "Pausado y contemplativo (planos largos, cámara lenta)",
    "light_color": "Frío azulado dominante con calidez puntual (ventana/farola ámbar)",
    "avoid": "Cliché navideño y dramatismo subrayado",
    "ending": "Abierto, eco emocional, sin resolver del todo",
    "refs": "Nieve, vaho, cristal empañado, lana; ciudad blanca; metáfora del lienzo en blanco",
}

style_attributes = [
    "paleta fría azul-gris con acentos cálidos ámbar puntuales",
    "alto key invernal, casi monocromo",
    "cámara estable y movimientos muy lentos",
    "planos largos contemplativos",
    "texturas táctiles: copos, vaho, cristal empañado, lana",
    "cierre abierto sin clímax dramático",
]

brief = (
    "Videoclip invernal inspirado en una nevada que paraliza la ciudad. Melancolía serena que "
    "evoluciona hacia un brote de esperanza: la nieve como lienzo en blanco para volver a empezar. "
    "Sin protagonista con rostro; la ciudad nevada y la propia nieve son los personajes. "
    "Frío azulado con calidez puntual. Evitar estética navideña y sentimentalismo."
)

# DIRQ-01: biblia visual estructurada (heurística desde la dirección).
bible = build_visual_bible(
    brief=brief,
    director_answers=director_answers,
    style_attributes=style_attributes,
    mood=director_answers["mood"],
)

# --- Planos enriquecidos (DIRQ-03): camera + movement + shot_size + intent ---
shots = [
    {
        "slug": "primer-copo",
        "shot_size": "primerísimo plano macro",
        "camera": "cámara fija, foco corto",
        "movement": "estática, cae el copo a cámara lenta",
        "action": "un solo copo se posa sobre asfalto oscuro; el negro se cubre de blanco",
        "notes": "apertura; sin rostro; respiración lenta; nada de clichés navideños",
        "intent": "abrir el clip con un gesto mínimo e hipnótico",
    },
    {
        "slug": "venas-ciudad",
        "shot_size": "plano general cenital",
        "camera": "cenital",
        "movement": "descenso de grúa/dron muy lento",
        "action": "calles vacías nevadas vistas desde arriba como venas blancas de la ciudad; solo huellas",
        "notes": "'cortan las venas de nuestra ciudad'; ciudad paralizada",
        "intent": "establecer la escala y el vacío urbano",
    },
    {
        "slug": "ventana-calida",
        "shot_size": "plano medio",
        "camera": "fijo desde el exterior, a través de cristal empañado",
        "movement": "estática, leve foco que respira",
        "action": "una ventana iluminada en ámbar sobre la fachada nevada; vaho en el cristal, una manta de lana entrevista",
        "notes": "única calidez del frame; interior cálido vs exterior frío; 'invita al sofá'",
        "intent": "introducir la primera chispa de calidez/esperanza",
    },
    {
        "slug": "nieva-sin-parar",
        "shot_size": "plano general",
        "camera": "estático, gran angular",
        "movement": "estática con nevada densa cruzando el cuadro",
        "action": "plaza urbana bajo nevada constante; una farola encendida; el tiempo parece detenido",
        "notes": "'hace ya meses que nieva sin parar'; suspensión temporal",
        "intent": "punto más bajo: quietud y peso emocional",
    },
    {
        "slug": "aliento-frio",
        "shot_size": "plano detalle",
        "camera": "a la altura del suelo, cámara fija",
        "movement": "estática, cristales formándose en time-lapse sutil",
        "action": "una nube de vaho cruza el encuadre helado; cristales de hielo se forman sobre una superficie",
        "notes": "'frío asombro, frío, helados calados'; textura táctil; sin protagonista",
        "intent": "intensificar el frío justo antes del giro",
    },
    {
        "slug": "lienzo-blanco",
        "shot_size": "plano medio",
        "camera": "plano medio",
        "movement": "travelling lateral muy lento",
        "action": "la nieve recién caída cubre una calle hasta volverla un lienzo blanco intacto; una sola huella se insinúa al fondo",
        "notes": "'pinta de blanco un lienzo para volver a empezar'; primer respiro de luz",
        "intent": "punto de giro: de melancolía a esperanza",
    },
    {
        "slug": "ciudad-blanca-eco",
        "shot_size": "plano general amplio",
        "camera": "cámara fija, leve desenfoque",
        "movement": "estática que se sostiene sin resolver",
        "action": "la ciudad entera blanca al amanecer; la nieve sigue cayendo suave; un punto de luz cálida late a lo lejos",
        "notes": "cierre abierto, eco emocional; 'blanca la triste ciudad'; esperanza latente",
        "intent": "cerrar en suspensión esperanzada, sin subrayar",
    },
]

lyrics = LYRICS_PATH.read_text(encoding="utf-8").strip() if LYRICS_PATH.is_file() else "(letra no encontrada)"
segments = propose_timed_segments(TOTAL_SEC, shots, title=TITLE, bible=bible)
costs = estimate_segment_costs_usd(segments)

R: list[str] = [
    f"# VideoZero — sesión guiada: {TITLE}",
    "",
    f"*Dirección por Claude (director IA) · prompting F6 por capas · {TOTAL_SEC:.0f}s · {len(shots)} planos.*",
    "",
    "## Letra",
    "",
    "```text",
    lyrics,
    "```",
    "",
    "## Dirección (respuestas del director)",
    "",
    "```json",
    json.dumps(director_answers, ensure_ascii=False, indent=2),
    "```",
    "",
    bible_to_markdown(bible).replace("# Biblia visual", "## Biblia visual (inyectada en cada plano)"),
    "",
    "## Planos con tiempo en la canción y prompting por capas",
    "",
    "> Cada prompt sigue el orden: sujeto+acción · cámara/movimiento · biblia (óptica/luz/paleta/grano) · negativos · aspect/duración.",
    "",
]

for seg in segments:
    sh = seg["shot"]
    sh_timed = {**sh, "duration_sec": seg["duration_sec"]}
    R += [
        f"### Plano {seg['index']} — {seg['start_sec']}s → {seg['end_sec']}s "
        f"({seg['duration_sec']}s) · `{sh['slug']}`",
        "",
        f"*Intención:* {sh.get('intent', '—')}",
        "",
        "**Kling** (sujeto-primero + cámara explícita)",
        "",
        compile_segment_prompt(sh_timed, "kling", bible=bible),
        "",
        "**Veo / genérico** (descriptivo cinematográfico + ambiente sonoro)",
        "",
        compile_segment_prompt(sh_timed, "generic", bible=bible),
        "",
        "**Runway** (movimiento claro, sin texto on-screen)",
        "",
        compile_segment_prompt(sh_timed, "runway", bible=bible),
        "",
        "---",
        "",
    ]

R += [
    "## Estimación de coste (USD, orientativa)",
    "",
    f"> {costs['disclaimer']}",
    "",
    "Tarifas (USD/s, configurables por `VIDEOZERO_EST_USD_PER_SEC_*`):",
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
    "## Recomendación de motor para este caso",
    "",
    "- **Kling** — mejor calidad/precio para planos contemplativos y consistencia de sujeto. Por defecto.",
    "- **Veo 3** — si quieres ambiente sonoro generado y máxima fidelidad cinematográfica (más caro).",
    "- **Runway Gen-4** — alternativa con control de movimiento de cámara claro.",
    "- Encadenado de keyframes (último frame → init-image del siguiente) recomendado para continuidad de nevada.",
    "",
]

report = "\n".join(R)

SEGMENTS_PATH = ROOT / "letras" / "filomena_segments.json"

if __name__ == "__main__":
    OUT_PATH.write_text(report, encoding="utf-8")
    SEGMENTS_PATH.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {len(segments)} segmentos · informe en {OUT_PATH}")
    print(f"[ok] segments.json en {SEGMENTS_PATH} (para `python -m app.render_cli --segments`)")
