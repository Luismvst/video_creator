"""
Biblia visual estructurada (DIRQ-01).

Una sola fuente de verdad de estilo/continuidad que se inyecta en CADA prompt
(capas), en lugar de planos sueltos sin coherencia. Funciona sin LLM (heurística
desde el brief / respuestas de dirección); el LLM solo mejora.

Campos: subject, world, palette, optics, light_rule, grain_dof,
style_attributes[], negatives[], aspect, default_duration_sec.

Reglas legales del repo: las referencias se traducen a ATRIBUTOS; nunca nombres
de obras, películas, artistas o marcas.
"""

from __future__ import annotations

from typing import Any, Optional

# Negativos base: válidos para cualquier videoclip generado por IA.
BASE_NEGATIVES: list[str] = [
    "texto en pantalla o subtítulos",
    "logotipos o marcas de agua",
    "deformidad de manos o rostros",
    "extremidades extra o anatomía imposible",
    "artefactos de compresión y parpadeo temporal",
]

DEFAULT_ASPECT = "16:9"
DEFAULT_DURATION_SEC = 4


def default_visual_bible() -> dict[str, Any]:
    """Biblia neutra: garantiza que incluso sin contexto los prompts sean cinematográficos."""
    return {
        "subject": "sujeto principal coherente con la letra (sin rostro reconocible si es simbólico)",
        "world": "espacio coherente con la letra",
        "palette": "paleta sobria y coherente, sin saturación excesiva",
        "optics": "lente 50mm, profundidad de campo media",
        "light_rule": "luz motivada, contraste suave",
        "grain_dof": "grano fino tipo 16mm, foco selectivo",
        "style_attributes": ["continuidad con la letra", "encuadres sencillos y legibles"],
        "negatives": list(BASE_NEGATIVES),
        "aspect": DEFAULT_ASPECT,
        "default_duration_sec": DEFAULT_DURATION_SEC,
    }


def _optics_for_pace(pace: str) -> str:
    p = (pace or "").lower()
    if any(k in p for k in ("paus", "lent", "slow", "contempl")):
        return "lente 85mm, profundidad de campo muy corta"
    if any(k in p for k in ("rápid", "rapid", "fast", "intens", "cortante")):
        return "lente 35mm, foco amplio y reactivo"
    return "lente 50mm, profundidad de campo media"


def _first_present(text: str, pairs: list[tuple[tuple[str, ...], str]], default: str) -> str:
    low = (text or "").lower()
    for keys, value in pairs:
        if any(k in low for k in keys):
            return value
    return default


def build_visual_bible(
    *,
    brief: str = "",
    lyrics: str = "",
    director_answers: Optional[dict[str, str]] = None,
    style_attributes: Optional[list[str]] = None,
    mood: Optional[str] = None,
) -> dict[str, Any]:
    """
    Construye la biblia visual de forma heurística a partir del brief y las
    respuestas de dirección. Determinista, sin red.
    """
    da = director_answers or {}
    blob = " ".join(
        [
            brief or "",
            mood or "",
            da.get("space", ""),
            da.get("light_color", ""),
            da.get("protagonist", ""),
            da.get("refs", ""),
            da.get("avoid", ""),
        ]
    )

    subject = da.get("protagonist") or "sujeto principal coherente con la letra"
    world = da.get("space") or _first_present(
        blob,
        [
            (("calle", "ciudad", "urban", "asfalto"), "exterior urbano"),
            (("interior", "casa", "sofá", "habitación"), "interior doméstico"),
            (("playa", "mar", "costa", "puerto"), "costa / horizonte"),
            (("bosque", "campo", "montaña", "naturaleza"), "naturaleza abierta"),
        ],
        "espacio coherente con la letra",
    )

    light_color = da.get("light_color") or ""
    palette = light_color or _first_present(
        blob,
        [
            (("neón", "neon"), "azul-magenta de neón con negros profundos"),
            (("nieve", "blanc", "invierno", "hielo"), "blancos y grises fríos con acentos cálidos puntuales"),
            (("cálid", "ámbar", "dorado", "atardecer"), "ámbar cálido y sombras suaves"),
            (("noche", "oscur"), "nocturna fría con luces puntuales"),
        ],
        "paleta sobria y coherente",
    )

    light_rule = _first_present(
        light_color or blob,
        [
            (("contraluz", "silueta"), "contraluz frío, atmósfera con niebla"),
            (("cálid", "ámbar", "ventana", "farola"), "luz fría dominante con focos cálidos motivados"),
            (("duro", "contraste", "sombra"), "claroscuro de contraste marcado"),
        ],
        "luz motivada y suave, sin sobreexposición",
    )

    optics = _optics_for_pace(da.get("visual_pace", ""))
    grain_dof = "grano fino tipo 16mm, foco selectivo y respiración de cámara mínima"

    attrs = list(style_attributes or [])
    if not attrs:
        attrs = ["continuidad con la letra", "encuadres sencillos y legibles", "movimiento de cámara contenido"]

    negatives = list(BASE_NEGATIVES)
    avoid = da.get("avoid") or ""
    if avoid:
        negatives.append(f"evitar: {avoid}")

    return {
        "subject": subject,
        "world": world,
        "palette": palette,
        "optics": optics,
        "light_rule": light_rule,
        "grain_dof": grain_dof,
        "style_attributes": attrs[:6],
        "negatives": negatives,
        "aspect": DEFAULT_ASPECT,
        "default_duration_sec": DEFAULT_DURATION_SEC,
    }


def bible_to_markdown(bible: dict[str, Any]) -> str:
    b = {**default_visual_bible(), **(bible or {})}
    lines = [
        "# Biblia visual",
        "",
        f"- **Sujeto:** {b['subject']}",
        f"- **Mundo / espacios:** {b['world']}",
        f"- **Paleta:** {b['palette']}",
        f"- **Óptica:** {b['optics']}",
        f"- **Regla de luz:** {b['light_rule']}",
        f"- **Grano / DOF:** {b['grain_dof']}",
        f"- **Aspect:** {b['aspect']} · **Duración base:** {b['default_duration_sec']}s",
        "",
        "**Atributos de estilo**",
        "",
    ]
    lines += [f"- {a}" for a in b.get("style_attributes", [])]
    lines += ["", "**Negativos (no debe aparecer)**", ""]
    lines += [f"- {n}" for n in b.get("negatives", [])]
    return "\n".join(lines)
