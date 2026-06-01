"""Sesión guiada (Claude como director IA) para 'Filomena'. Throwaway UAT script."""
from __future__ import annotations

import json
from pathlib import Path

from app.timed_segments import propose_timed_segments
from app.video_cost_estimate import estimate_segment_costs_usd

TITLE = "Filomena"
TOTAL_SEC = 120.0

LYRICS_PATH = Path(__file__).resolve().parent.parent / "letras" / "filomena_bucero.txt"
OUT_PATH = Path(__file__).resolve().parent.parent / "letras" / "filomena_session.md"

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

creative_intake = {
    "reference_notes": (
        "Videoclip invernal inspirado en una nevada que paraliza la ciudad (tipo Filomena). "
        "Tono de melancolía serena que evoluciona hacia un brote de esperanza: la nieve como "
        "'lienzo en blanco para volver a empezar'. Sin protagonista con rostro; la ciudad nevada "
        "y la propia nieve son los personajes. Evitar estética navideña y sentimentalismo. "
        "Sin nombres de obras, artistas ni películas reales."
    ),
    "style_attributes": [
        "paleta fría azul-gris con acentos cálidos ámbar puntuales",
        "alto key invernal, casi monocromo",
        "cámara estable y movimientos muy lentos",
        "planos largos contemplativos",
        "texturas táctiles: copos, vaho, cristal empañado, lana",
        "cierre abierto sin clímax dramático",
    ],
}

# --- Planos (autoría del director IA) ---
shots = [
    {
        "slug": "primer-copo",
        "camera": "primerísimo plano macro, cámara fija, foco corto",
        "action": "un solo copo cae a cámara lenta y se posa sobre asfalto oscuro; el negro se cubre de blanco",
        "notes": "apertura; sin rostro; respiración lenta; frío azulado; nada de clichés navideños",
    },
    {
        "slug": "venas-ciudad",
        "camera": "plano cenital lento, descenso suave de grúa/dron",
        "action": "calles vacías nevadas vistas desde arriba como venas blancas de la ciudad; solo huellas, ninguna figura",
        "notes": "'cortan las venas de nuestra ciudad'; ciudad paralizada; gris plomizo",
    },
    {
        "slug": "ventana-calida",
        "camera": "plano medio fijo desde el exterior, a través de cristal empañado",
        "action": "una ventana iluminada en ámbar sobre la fachada nevada; vaho en el cristal, una manta de lana entrevista; nadie visible",
        "notes": "única calidez del frame; interior cálido vs exterior frío; 'mece las penas e invita al sofá'",
    },
    {
        "slug": "nieva-sin-parar",
        "camera": "plano general estático, gran angular",
        "action": "plaza urbana bajo nevada densa y constante; una farola encendida; el tiempo parece detenido",
        "notes": "'hace ya meses que nieva sin parar'; suspensión temporal; calidez puntual de la farola",
    },
    {
        "slug": "aliento-frio",
        "camera": "plano detalle a la altura del suelo, cámara fija",
        "action": "una nube de vaho cruza el encuadre helado; cristales de hielo se forman sobre una superficie",
        "notes": "'frío asombro, frío, helados calados'; textura táctil; sin protagonista",
    },
    {
        "slug": "lienzo-blanco",
        "camera": "plano medio, travelling lateral muy lento",
        "action": "la nieve recién caída cubre una calle hasta volverla un lienzo blanco intacto; una sola huella se insinúa al fondo",
        "notes": "'pinta de blanco un lienzo para volver a empezar'; punto de giro hacia la esperanza; primer respiro de luz",
    },
    {
        "slug": "ciudad-blanca-eco",
        "camera": "plano general amplio, cámara fija, leve desenfoque",
        "action": "la ciudad entera blanca al amanecer; la nieve sigue cayendo suave y el plano se sostiene sin resolverse; un punto de luz cálida late a lo lejos",
        "notes": "cierre abierto, eco emocional; 'blanca la triste ciudad'; esperanza latente, no subrayada",
    },
]

lyrics = LYRICS_PATH.read_text(encoding="utf-8").strip() if LYRICS_PATH.is_file() else "(letra no encontrada)"
segments = propose_timed_segments(TOTAL_SEC, shots, title=TITLE)
costs = estimate_segment_costs_usd(segments)

R: list[str] = [
    f"# VideoZero — sesión guiada: {TITLE}",
    "",
    f"*Dirección generada por Claude (modo director IA) sobre {TOTAL_SEC:.0f}s · {len(shots)} planos.*",
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
    "## Intake creativo",
    "",
    "```json",
    json.dumps(creative_intake, ensure_ascii=False, indent=2),
    "```",
    "",
    "## Planos con tiempo en la canción y promptings",
    "",
]

for seg in segments:
    idx = seg["index"]
    R += [
        f"### Plano {idx} — {seg['start_sec']}s → {seg['end_sec']}s (duración {seg['duration_sec']}s) · `{seg['shot']['slug']}`",
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

R += [
    "## Estimación de coste (USD, orientativa)",
    "",
    f"> {costs['disclaimer']}",
    "",
    "Tarifas usadas (USD/s, configurables por `VIDEOZERO_EST_USD_PER_SEC_*`):",
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

report = "\n".join(R)
OUT_PATH.write_text(report, encoding="utf-8")
print(report)
print(f"\n[guardado] {OUT_PATH}")
