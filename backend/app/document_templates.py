from __future__ import annotations

from typing import Any, Optional


def _pacing_note(pacing: Optional[str]) -> str:
    if not pacing:
        return "Sin perfil de pacing definido (por defecto: ritmo equilibrado en planificación)."
    return {
        "slow_cinematic": "Pacing: lento / cinematográfico — priorizar planos largos y respiro.",
        "balanced": "Pacing: equilibrado — alternancia moderada de densidad visual.",
        "fast_intense": "Pacing: rápido / intenso — cortes frecuentes, alta densidad de información.",
        "minimal": "Pacing: mínimo / aire — pocos elementos, énfasis en silencio visual.",
    }.get(pacing, f"Pacing: {pacing}")


def build_visual_bible_markdown(
    *,
    title: Optional[str],
    artist: Optional[str],
    pacing_profile: Optional[str],
    sections: list[dict[str, Any]],
    insights: list[dict[str, Any]],
    intake: dict[str, Any],
    locked: bool,
) -> str:
    lines: list[str] = [
        "# Visual Bible",
        "",
        f"**Estado:** {'Bloqueado (Creative Lock)' if locked else 'Borrador — edita y bloquea cuando cierres dirección.'}",
        "",
        "## Identidad del clip",
        "",
        f"- **Título:** {title or '—'}",
        f"- **Artista:** {artist or '—'}",
        f"- **{_pacing_note(pacing_profile)}**",
        "",
        "## Referencias → atributos (intake)",
        "",
    ]
    notes = intake.get("reference_notes") or "(sin notas)"
    attrs = intake.get("style_attributes") or []
    lines.append(str(notes))
    if isinstance(attrs, list) and attrs:
        lines.append("")
        lines.append("Atributos de estilo (no literales de obras reales):")
        for a in attrs:
            lines.append(f"- {a}")
    lines.extend(["", "## Secciones de letra (ancla)", ""])
    for s in sections:
        lines.append(
            f"- **{s.get('label', '?')}** ({s.get('kind', '')}) — líneas {s.get('start_line_index')}–{s.get('end_line_index')}",
        )
    lines.extend(["", "## Ideas visuales (LYR)", ""])
    if not insights:
        lines.append("(sin ideas guardadas)")
    else:
        for i in insights:
            lines.append(f"- **{i.get('category', '')}:** {i.get('text', '')}")
    lines.extend(
        [
            "",
            "## Continuidad",
            "",
            "- Heredar siempre de sección + idea + intake; evitar prompts aislados.",
            "",
        ],
    )
    return "\n".join(lines)


def build_treatment_markdown(
    *,
    title: Optional[str],
    artist: Optional[str],
    pacing_profile: Optional[str],
    sections: list[dict[str, Any]],
    director_answers: dict[str, Any],
    routes: list[dict[str, Any]],
    selected_route_id: Optional[str],
    locked: bool,
) -> str:
    lines: list[str] = [
        "# Treatment (tono profesional)",
        "",
        f"**Estado:** {'Congelado con Creative Lock' if locked else 'Borrador'}",
        "",
        "## Logline",
        "",
        f"Videoclip para **{title or 'canción sin título'}** de **{artist or 'artista'}**, guiado por la letra y un "
        f"enfoque {_pacing_note(pacing_profile).lower()}",
        "",
        "## Dirección (cuestionario resumido)",
        "",
    ]
    if not director_answers:
        lines.append("(sin respuestas guardadas en el cuestionario)")
    else:
        for k, v in director_answers.items():
            lines.append(f"- **{k}:** {v}")
    lines.extend(["", "## Rutas creativas", ""])
    if not routes:
        lines.append("(sin rutas definidas)")
    else:
        for r in routes:
            rid = r.get("id", "")
            mark = "✓ " if selected_route_id and rid == selected_route_id else ""
            lines.append(f"- {mark}**{r.get('title', rid)}:** {r.get('summary', '')}")
    lines.extend(
        [
            "",
            "## Estructura narrativa (secciones)",
            "",
        ],
    )
    for s in sections:
        lines.append(f"- {s.get('label', '?')}: ancla líneas {s.get('start_line_index')}–{s.get('end_line_index')}.")
    lines.extend(["", "---", "", "*Documento generado por VideoZero (MVP). Edita en la app y vuelve a exportar.*"])
    return "\n".join(lines)
