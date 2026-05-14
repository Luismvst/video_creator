from __future__ import annotations

from typing import Any


def compile_prompt_markdown(shots: list[dict[str, Any]], provider: str) -> str:
    """PRM-01..03 MVP: canonical-ish lines per shot; no copyrighted names in output."""
    header = {
        "generic": "# Prompt pack — genérico cinematográfico",
        "runway": "# Prompt pack — orientado Runway (MVP)",
        "kling": "# Prompt pack — orientado Kling (MVP)",
    }.get(provider, f"# Prompt pack — {provider}")

    lines: list[str] = [
        header,
        "",
        "> Atributos de estilo y continuidad deben venir de la Visual Bible; no pegar obras o artistas identificables.",
        "",
    ]
    if not shots:
        lines.append("(No hay shots en `shots_json`. Añade filas JSON en la UI Plan o pega un array `[{...}]`.)")
        return "\n".join(lines)

    for idx, sh in enumerate(shots, start=1):
        slug = sh.get("slug") or f"shot-{idx}"
        cam = sh.get("camera") or ""
        act = sh.get("action") or ""
        notes = sh.get("notes") or ""
        lines.append(f"## {idx}. {slug}")
        lines.append("")
        if provider == "runway":
            lines.append(
                f"Texto sugerido: {act} — {cam}. Continuidad: {notes}. "
                "Evitar texto on-screen ilegible; priorizar movimiento de cámara claro.",
            )
        elif provider == "kling":
            lines.append(
                f"Prompt: {act}. Lente/encuadre: {cam}. Notas: {notes}. "
                "Mantener sujeto principal estable entre cortes adyacentes cuando aplique.",
            )
        else:
            lines.append(f"Plano: {act}\n\nCámara / encuadre: {cam}\n\nContinuidad / revisión: {notes}")
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
