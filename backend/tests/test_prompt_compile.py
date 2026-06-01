"""DIRQ-01/02/06: biblia visual + prompt por capas + tuning por proveedor."""

from app.prompt_compile import compile_prompt_markdown, compile_segment_prompt
from app.visual_bible import build_visual_bible, default_visual_bible

SHOT = {
    "slug": "lienzo-blanco",
    "camera": "plano medio",
    "movement": "travelling lateral lento",
    "action": "la nieve cubre una calle hasta volverla un lienzo blanco",
    "notes": "punto de giro hacia la esperanza",
    "duration_sec": 6,
}


def test_bible_has_structured_fields() -> None:
    b = build_visual_bible(
        brief="ciudad nevada, frío con calidez puntual",
        director_answers={"visual_pace": "pausado", "light_color": "frío azulado", "avoid": "cliché navideño"},
    )
    for key in ("subject", "world", "palette", "optics", "light_rule", "grain_dof", "negatives", "aspect"):
        assert key in b
    assert b["negatives"]
    # 'avoid' se propaga a negativos.
    assert any("cliché" in n for n in b["negatives"])
    # pausado → óptica de DOF corto (85mm).
    assert "85mm" in b["optics"]


def test_layered_prompt_contains_all_layers() -> None:
    b = default_visual_bible()
    p = compile_segment_prompt(SHOT, "generic", bible=b)
    # acción (sujeto)
    assert "lienzo blanco" in p
    # cámara + movimiento
    assert "travelling lateral lento" in p
    # biblia: óptica + paleta
    assert b["optics"].split(",")[0] in p
    assert "paleta" in p
    # negativos
    assert "Negativos:" in p
    # aspect + duración del plano
    assert "16:9" in p and "6s" in p


def test_provider_tuning_differs() -> None:
    b = default_visual_bible()
    kling = compile_segment_prompt(SHOT, "kling", bible=b)
    runway = compile_segment_prompt(SHOT, "runway", bible=b)
    generic = compile_segment_prompt(SHOT, "generic", bible=b)
    assert kling != runway != generic
    # Runway insiste en evitar texto on-screen.
    assert "on-screen" in runway.lower() or "on-screen" in runway
    # Kling pide estabilidad de sujeto entre cortes.
    assert "estable" in kling.lower()
    # Genérico/Veo añade ambiente sonoro.
    assert "sonoro" in generic.lower()


def test_markdown_pack_keeps_per_shot_header_and_bible() -> None:
    md = compile_prompt_markdown([SHOT], "kling", bible=default_visual_bible())
    assert "## 1. lienzo-blanco" in md
    assert "Biblia:" in md  # biblia resumida en cabecera del pack


def test_empty_shots_is_safe() -> None:
    md = compile_prompt_markdown([], "generic")
    assert "No hay shots" in md
