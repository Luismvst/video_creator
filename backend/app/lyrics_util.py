from __future__ import annotations

from typing import Optional, Protocol


class _SectionSpanLike(Protocol):
    label: str
    start_line_index: int
    end_line_index: int


SECTION_KINDS = frozenset({"intro", "verse", "chorus", "bridge", "hook", "outro", "custom"})
PACING_PROFILES = frozenset({"slow_cinematic", "balanced", "fast_intense", "minimal"})


def split_lyric_lines(lyrics_text: Optional[str]) -> list[str]:
    if lyrics_text is None:
        return []
    return lyrics_text.splitlines()


def lyric_line_count(lyrics_text: Optional[str]) -> int:
    return len(split_lyric_lines(lyrics_text))


def validate_section_span(lyrics_text: Optional[str], start_line_index: int, end_line_index: int) -> None:
    n = lyric_line_count(lyrics_text)
    if n == 0:
        raise ValueError("Save non-empty lyrics before using sections.")
    if start_line_index < 0 or end_line_index < 0:
        raise ValueError("Line indices must be non-negative.")
    if start_line_index > end_line_index:
        raise ValueError("start_line_index must be <= end_line_index.")
    if end_line_index >= n:
        raise ValueError(f"Line indices must be within 0..{n - 1} for the current lyrics.")


def structure_warnings(lyrics_text: Optional[str], sections: list[_SectionSpanLike]) -> list[str]:
    """Read-model checks: invalid spans vs saved lyrics (does not mutate)."""
    if not sections:
        return []
    n = lyric_line_count(lyrics_text)
    if n == 0:
        return [
            "Hay secciones guardadas pero la letra está vacía; define y guarda la letra para validar rangos de línea.",
        ]
    out: list[str] = []
    max_i = n - 1
    for s in sections:
        if s.start_line_index > s.end_line_index:
            out.append(
                f"Sección «{s.label}»: el inicio ({s.start_line_index}) es mayor que el fin ({s.end_line_index}).",
            )
        if s.start_line_index < 0 or s.end_line_index < 0:
            out.append(f"Sección «{s.label}»: índices de línea negativos.")
        if s.end_line_index > max_i or s.start_line_index > max_i:
            out.append(
                f"Sección «{s.label}» (líneas {s.start_line_index}–{s.end_line_index}): "
                f"fuera del rango de la letra guardada (0–{max_i}).",
            )
    return out
