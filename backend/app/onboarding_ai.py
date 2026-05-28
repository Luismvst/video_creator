from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

from .lyrics_insights_engine import _openai_api_key, _openai_model, openai_configured


def _split_lines(text: str) -> list[str]:
    return (text or "").splitlines()


def suggest_section_spans(lyrics_text: str) -> list[tuple[str, str, int, int]]:
    """Stanzas separadas por líneas en blanco → (label, kind, start_line_index, end_line_index)."""
    raw = _split_lines(lyrics_text)
    if not raw:
        return []
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(raw)
    while i < n:
        while i < n and not raw[i].strip():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and raw[i].strip():
            i += 1
        spans.append((start, i - 1))

    if not spans:
        return []
    if len(spans) == 1:
        return [("Canción", "verse", spans[0][0], spans[0][1])]
    out: list[tuple[str, str, int, int]] = []
    for idx, (a, b) in enumerate(spans, start=1):
        label = f"Bloque {idx}" if len(spans) > 2 else ("Apertura" if idx == 1 else "Cierre")
        kind = "verse" if idx < len(spans) else "chorus"
        out.append((label, kind, a, b))
    return out


def _keyword_attrs(brief: str) -> list[str]:
    brief_l = brief.lower()
    pool = [
        ("neón", "luz neón / reflejos"),
        ("neon", "luz neón / reflejos"),
        ("noche", "estética nocturna"),
        ("lluvia", "lluvia / humedad"),
        ("coche", "interior o exterior de coche"),
        ("carretera", "carretera / movimiento"),
        ("casa", "espacio doméstico"),
        ("playa", "costa / horizonte"),
        ("baile", "cuerpo / movimiento"),
        ("sombra", "sombras marcadas"),
        ("color", "paleta expresiva"),
    ]
    found: list[str] = []
    for kw, attr in pool:
        if kw in brief_l and attr not in found:
            found.append(attr)
        if len(found) >= 5:
            break
    if not found:
        found = ["atmósfera íntima", "encuadres sencillos", "continuidad con la letra"]
    return found[:5]


def heuristic_onboarding_package(
    lyrics_text: str,
    brief: str,
    *,
    title: Optional[str],
    mood: Optional[str],
) -> dict[str, str]:
    """Build JSON string fields for Song without LLM."""
    brief = (brief or "").strip()
    b_low = brief.lower()
    notes = (
        brief[:1200]
        if brief
        else "Aún no hay descripción libre: el usuario puede volver al paso anterior y escribir su visión."
    )
    attrs = _keyword_attrs(brief) if brief else ["guiado por la letra", "sin referencias literales a obras reales"]
    intake = {"reference_notes": notes, "style_attributes": attrs}
    director = {
        "visual_density": "media",
        "color_bible": "derivada de la letra y la visión descrita (sin copiar paletas de terceros)",
        "protagonist_energy": "contenida" if "íntim" in b_low or "solo" in b_low else "media",
        "ending_tone": "abierta / emocional",
        "camera_language": "cámara estable con algún plano secuencia suave",
    }
    if mood:
        director["mood_objetivo"] = mood
    if title:
        director["titulo_trabajo"] = title

    r_a = (
        brief[:200] + "…"
        if len(brief) > 200
        else (brief or "Intimidad y lectura lenta de la letra.")
    )
    r_b = "Alternativa más dinámica: fragmentar el montaje y jugar con el espacio urbano."
    routes = {
        "routes": [
            {"id": "route-a", "title": "Ruta A — íntima y pausada", "summary": r_a},
            {"id": "route-b", "title": "Ruta B — más urbana y cortante", "summary": r_b},
        ]
    }
    plan = [
        {"title": "1. Revisar letra y secciones", "detail": "Confirmar que la estructura refleja la canción."},
        {"title": "2. Bloquear dirección", "detail": "Creative Lock cuando estés conforme."},
        {"title": "3. Exportar y generar fuera", "detail": "Usar bundle + prompts en tu herramienta de vídeo."},
    ]
    shots = [
        {
            "slug": "apertura",
            "camera": "plano medio suave",
            "action": "presentar al protagonista o espacio principal alineado con la primera imagen de la letra",
            "notes": "heredar atributos de estilo sugeridos",
        },
        {
            "slug": "giro",
            "camera": "corte a detalle simbólico",
            "action": "refuerzo visual del giro emocional del segundo bloque",
            "notes": "sin texto ilegible en pantalla",
        },
    ]
    return {
        "creative_intake_json": json.dumps(intake, ensure_ascii=False),
        "director_answers_json": json.dumps(director, ensure_ascii=False),
        "creative_routes_json": json.dumps(routes, ensure_ascii=False),
        "selected_route_id": "route-a",
        "generation_plan_json": json.dumps(plan, ensure_ascii=False),
        "shots_json": json.dumps(shots, ensure_ascii=False),
    }


def llm_onboarding_package(
    lyrics_text: str,
    brief: str,
    *,
    title: Optional[str],
    mood: Optional[str],
    language: Optional[str],
    timeout_sec: float = 60.0,
) -> tuple[Optional[dict[str, str]], Optional[str]]:
    """Returns (same keys as heuristic_onboarding_package, str JSON values) or (None, error)."""
    key = _openai_api_key()
    if not key:
        return None, "No API key"

    meta = f"Título: {title or '—'}\nMood: {mood or '—'}\nIdioma: {language or '—'}\n"
    user = (
        meta
        + "Visión del usuario (brief):\n---\n"
        + brief.strip()[:6000]
        + "\n---\nLetra:\n---\n"
        + lyrics_text.strip()[:8000]
        + "\n---\n"
        "Devuelve SOLO un JSON con esta forma exacta de claves:\n"
        '{"intake":{"reference_notes":"str","style_attributes":["str",...]},'
        '"director":{"visual_density":"str","color_bible":"str","protagonist_energy":"str","ending_tone":"str","camera_language":"str"},'
        '"routes":[{"id":"str","title":"str","summary":"str"},...],'
        '"selected_route_id":"str",'
        '"generation_plan":[{"title":"str","detail":"str"},...],'
        '"shots":[{"slug":"str","camera":"str","action":"str","notes":"str"},...]}\n'
        "2 o 3 rutas; 4–6 atributos de estilo como frases cortas (sin nombres de obras o artistas reales); textos en español."
    )

    body = json.dumps(
        {
            "model": _openai_model(),
            "temperature": 0.45,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Eres director creativo de videoclips. Respondes únicamente con JSON válido.",
                },
                {"role": "user", "content": user},
            ],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:500]
        except OSError:
            detail = str(e)
        return None, f"OpenAI HTTP {e.code}: {detail}"
    except Exception as e:  # noqa: BLE001
        return None, f"OpenAI: {e}"

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None, "Respuesta OpenAI inesperada."

    content = (content or "").strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None, "JSON inválido del modelo."

    try:
        intake = data["intake"]
        director = data["director"]
        routes = data["routes"]
        sel = str(data.get("selected_route_id") or "route-a")
        plan = data.get("generation_plan") or []
        shots = data.get("shots") or []
        if not isinstance(intake, dict) or not isinstance(director, dict):
            return None, "Estructura intake/director incorrecta."
        if not isinstance(routes, list) or len(routes) < 2:
            return None, "Se esperaban al menos 2 rutas."
        wrapped = {"routes": routes}
        return {
            "creative_intake_json": json.dumps(intake, ensure_ascii=False),
            "director_answers_json": json.dumps(director, ensure_ascii=False),
            "creative_routes_json": json.dumps(wrapped, ensure_ascii=False),
            "selected_route_id": sel,
            "generation_plan_json": json.dumps(plan, ensure_ascii=False),
            "shots_json": json.dumps(shots, ensure_ascii=False),
        }, None
    except (KeyError, TypeError) as e:
        return None, f"JSON incompleto: {e}"


def build_onboarding_package(
    lyrics_text: str,
    brief: str,
    *,
    title: Optional[str],
    mood: Optional[str],
    language: Optional[str],
    prefer_llm: bool,
) -> tuple[dict[str, str], str]:
    """
    Returns (patch_dict with JSON string fields, note).
    prefer_llm: try OpenAI first when configured; always fall back to heuristic on failure.
    """
    if prefer_llm and openai_configured():
        pkg, err = llm_onboarding_package(lyrics_text, brief, title=title, mood=mood, language=language)
        if pkg:
            return pkg, "Dirección generada con IA (OpenAI)."
        h = heuristic_onboarding_package(lyrics_text, brief, title=title, mood=mood)
        return h, f"Heurística local (IA no disponible o falló: {err or 'motivo desconocido'})."
    h = heuristic_onboarding_package(lyrics_text, brief, title=title, mood=mood)
    if prefer_llm and not openai_configured():
        return h, "Heurística local (pediste IA pero no hay clave OpenAI configurada)."
    return h, "Heurística local (modo heurístico o sin IA)."
