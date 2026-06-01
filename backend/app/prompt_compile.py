"""
Compilador de prompts por CAPAS y con tuning por proveedor (DIRQ-02 / DIRQ-06).

Orden de capas en cada prompt:
  [sujeto + acción de la línea] + [cámara / movimiento] +
  [biblia: óptica / luz / paleta / grano-DOF] + [negativos] + [aspect / duración]

La biblia visual (DIRQ-01) se inyecta en CADA prompt para garantizar coherencia.
Si no se pasa biblia, se usa una neutra para que el prompt siga siendo cinematográfico.

Compatibilidad: `compile_prompt_markdown(shots, provider)` mantiene la firma previa
(el parámetro `bible` es opcional) y conserva el header `## N. slug` por plano.
"""

from __future__ import annotations

from typing import Any, Optional

from .visual_bible import default_visual_bible


def _bible(bible: Optional[dict[str, Any]]) -> dict[str, Any]:
    return {**default_visual_bible(), **(bible or {})}


def _negatives_str(b: dict[str, Any]) -> str:
    return ", ".join(b.get("negatives", [])) or "texto en pantalla, marcas de agua"


def _camera_layer(sh: dict[str, Any]) -> str:
    cam = (sh.get("camera") or "").strip()
    mov = (sh.get("movement") or "").strip()
    size = (sh.get("shot_size") or "").strip()
    parts = [p for p in (size, cam, mov) if p]
    return ", ".join(parts) if parts else "encuadre estable"


def _tech_layer(sh: dict[str, Any], b: dict[str, Any]) -> str:
    dur = sh.get("duration_sec") or b.get("default_duration_sec")
    return f"{b['aspect']}, {dur}s"


def compile_segment_prompt(sh: dict[str, Any], provider: str, bible: Optional[dict[str, Any]] = None) -> str:
    """Prompt por capas de un único plano, afinado al proveedor."""
    b = _bible(bible)
    action = (sh.get("action") or sh.get("slug") or "plano coherente con la letra").strip()
    camera = _camera_layer(sh)
    notes = (sh.get("notes") or "").strip()
    optics = b["optics"]
    light = b["light_rule"]
    palette = b["palette"]
    grain = b["grain_dof"]
    neg = _negatives_str(b)
    tech = _tech_layer(sh, b)
    look = f"óptica: {optics}; luz: {light}; paleta: {palette}; {grain}"

    if provider == "kling":
        # Kling: sujeto-primero + cámara explícita.
        return (
            f"{action}. Cámara: {camera}. {look}. "
            f"Continuidad: {notes or 'heredar biblia visual'}. "
            f"Negativos: {neg}. {tech}. "
            "Mantener el sujeto estable entre cortes adyacentes."
        )
    if provider == "runway":
        # Runway: movimiento de cámara claro, sin texto on-screen.
        return (
            f"Texto sugerido: {action} — {camera}. {look}. "
            f"Continuidad: {notes or 'heredar biblia visual'}. "
            f"Negativos: {neg}. Priorizar movimiento de cámara legible y evitar texto on-screen. {tech}."
        )
    # generic (lo consume también Veo): descriptivo cinematográfico + ambiente sonoro.
    world = b.get("world", "")
    return (
        f"{action}"
        + (f", en {world}" if world else "")
        + f". {camera}. {look}. "
        f"Ambiente sonoro coherente con la escena (sin música licenciada ni voces reconocibles). "
        f"Continuidad: {notes or 'heredar biblia visual'}. "
        f"Negativos: {neg}. {tech}."
    )


def compile_prompt_markdown(
    shots: list[dict[str, Any]],
    provider: str,
    bible: Optional[dict[str, Any]] = None,
) -> str:
    """PRM/DIRQ-02: prompt pack por capas, un bloque por plano, afinado al proveedor."""
    header = {
        "generic": "# Prompt pack — genérico cinematográfico (capas)",
        "runway": "# Prompt pack — Runway (capas)",
        "kling": "# Prompt pack — Kling (capas)",
        "veo": "# Prompt pack — Veo (capas)",
        "veo3": "# Prompt pack — Veo (capas)",
    }.get(provider, f"# Prompt pack — {provider} (capas)")

    b = _bible(bible)
    lines: list[str] = [
        header,
        "",
        "> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.",
        f"> Biblia: óptica {b['optics']} · luz {b['light_rule']} · paleta {b['palette']} · {b['aspect']}.",
        "",
    ]
    if not shots:
        lines.append("(No hay shots en `shots_json`. Añade filas `[{slug,camera,action,notes}]`.)")
        return "\n".join(lines)

    # Veo lee el campo genérico en render_client; normalizamos.
    prov = "generic" if provider in ("veo", "veo3", "veo3_fast", "wan") else provider
    for idx, sh in enumerate(shots, start=1):
        slug = sh.get("slug") or f"shot-{idx}"
        lines.append(f"## {idx}. {slug}")
        lines.append("")
        lines.append(compile_segment_prompt(sh, prov, bible=b))
        lines.append("")
    return "\n".join(lines)


def build_generation_plan_markdown(steps: list[dict[str, Any]]) -> str:
    lines = ["# Plan de generación (MVP)", ""]
    if not steps:
        lines.append("(Vacío — define pasos en `generation_plan_json` como lista `{title, detail}`. )")
        return "\n".join(lines)
    for i, st in enumerate(steps, start=1):
        lines.append(f"{i}. **{st.get('title', 'Paso')}** — {st.get('detail', '')}")
    return "\n".join(lines)
