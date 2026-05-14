from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from typing import Literal, Optional

INSIGHT_CATEGORIES = frozenset({"motif", "symbol", "place", "hook"})
InsightCategory = Literal["motif", "symbol", "place", "hook"]

_STOP = frozenset(
    """
    el la los las un una unos unas y o u de del al a en por para con sin sobre entre
    que como cuando donde quien yo tu ello nos vos ellos ellas me te se lo le les mi su
    the a an and or of to in on at as is are was were be been being it this that these those
    from with without into about after before than then not no yes si tu tus mi mis
    hay muy mas menos todo todas todo todos algo nadie alguien cada otro otra otros otras
    """.split()
)

_PLACE_HINTS = (
    "calle",
    "ciudad",
    "pueblo",
    "barrio",
    "mar",
    "río",
    "rio",
    "cielo",
    "noche",
    "día",
    "dia",
    "habitación",
    "habitacion",
    "cuarto",
    "sala",
    "cocina",
    "ventana",
    "puerta",
    "carretera",
    "room",
    "city",
    "town",
    "street",
    "sky",
    "sea",
    "ocean",
    "night",
    "day",
    "window",
    "door",
    "kitchen",
    "bedroom",
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text.lower())


def heuristic_insights(lyrics_text: str, max_items: int = 14) -> list[tuple[InsightCategory, str]]:
    raw = (lyrics_text or "").strip()
    if not raw:
        return []
    items: list[tuple[InsightCategory, str]] = []
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    toks = [t for t in _tokens(raw) if t not in _STOP and len(t) > 2]
    for word, c in Counter(toks).most_common(6):
        if c >= 2:
            items.append(("motif", f"Palabra recurrente: «{word}» ({c}×)"))
        if len(items) >= max_items:
            return items

    seen_place_kw: set[str] = set()
    for line in lines:
        low = line.lower()
        for kw in _PLACE_HINTS:
            if kw in low and kw not in seen_place_kw:
                snippet = line if len(line) <= 140 else line[:137] + "…"
                items.append(("place", f"Ancla de lugar («{kw}»): {snippet}"))
                seen_place_kw.add(kw)
                break
        if len(items) >= max_items:
            return items

    hooks = 0
    for line in lines:
        if "?" in line and len(line) <= 220:
            items.append(("hook", line if len(line) <= 200 else line[:197] + "…"))
            hooks += 1
        if hooks >= 3:
            break
        if len(items) >= max_items:
            return items

    symbols = 0
    for line in lines:
        for w in re.findall(r"\b[A-ZÁÉÍÓÚÜÑ]{2,}\b", line):
            if w.lower() in _STOP:
                continue
            items.append(("symbol", f"Énfasis / bloque en mayúsculas: {w}"))
            symbols += 1
            if symbols >= 3:
                break
        if symbols >= 3:
            break
        if len(items) >= max_items:
            return items

    if not items and lines:
        first = lines[0]
        items.append(("hook", f"Línea de apertura (gancho narrativo): {first[:180]}"))

    return items[:max_items]


def _openai_api_key() -> Optional[str]:
    return os.getenv("VIDEOZERO_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")


def openai_configured() -> bool:
    return bool(_openai_api_key())


def _openai_model() -> str:
    return os.getenv("VIDEOZERO_OPENAI_MODEL", "gpt-4o-mini")


def llm_insights(
    lyrics_text: str,
    *,
    title: Optional[str],
    mood: Optional[str],
    language: Optional[str],
    timeout_sec: float = 45.0,
) -> tuple[list[tuple[InsightCategory, str]], Optional[str]]:
    """Returns (items, error_note). On hard failure, error_note is set and items may be empty."""
    key = _openai_api_key()
    if not key:
        return [], "No API key configured (set VIDEOZERO_OPENAI_API_KEY or OPENAI_API_KEY)."

    meta = f"Título: {title or '—'}\nMood: {mood or '—'}\nIdioma: {language or '—'}\n"
    user_prompt = (
        meta
        + "Letra:\n---\n"
        + lyrics_text.strip()[:12000]
        + "\n---\n"
        "Devuelve SOLO JSON: {\"items\":[{\"category\":\"motif|symbol|place|hook\",\"text\":\"...\"}]}. "
        "Entre 6 y 12 ítems en español, sin nombres de obras o artistas reales; "
        "motifs/símbolos/lugares/ganchos interpretativos útiles para dirección de videoclip."
    )

    body = json.dumps(
        {
            "model": _openai_model(),
            "temperature": 0.6,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un director creativo. Respondes únicamente con JSON válido.",
                },
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
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
        return [], f"OpenAI HTTP {e.code}: {detail}"
    except Exception as e:  # noqa: BLE001 — surface to caller
        return [], f"OpenAI request failed: {e}"

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return [], "Unexpected OpenAI response shape."

    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        data = json.loads(content)
        raw_items = data.get("items", [])
    except json.JSONDecodeError:
        return [], "OpenAI returned non-JSON content."

    out: list[tuple[InsightCategory, str]] = []
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        cat = str(it.get("category", "")).strip()
        text = str(it.get("text", "")).strip()
        if cat not in INSIGHT_CATEGORIES or not text:
            continue
        if len(text) > 480:
            text = text[:477] + "…"
        out.append((cat, text))  # type: ignore[arg-type]
        if len(out) >= 14:
            break

    if not out:
        return [], "OpenAI JSON contained no valid items."
    return out, None
