"""Tests del planner temporal real (v2-F2). Puros: sin audio ni binarios."""

from app.music_planner import (
    _merge_min,
    _split_max,
    _to_intervals,
    plan_segments_from_timings,
    plan_timeline,
)

SHOTS = [
    {"slug": "a", "camera": "wide", "action": "open", "notes": "n1"},
    {"slug": "b", "camera": "close", "action": "detail", "notes": "n2"},
    {"slug": "c", "camera": "medium", "action": "bridge", "notes": "n3"},
]


def _timings(starts_ends):
    return [
        {"line_index": i, "line": f"linea {i}", "start": s, "end": e}
        for i, (s, e) in enumerate(starts_ends)
    ]


def test_to_intervals_contiguous_and_covers_total() -> None:
    segs = _to_intervals([2.0, 5.0, 9.0], total=12.0)
    # prepende 0.0 y cierra en total
    assert segs[0][0] == 0.0
    assert segs[-1][1] == 12.0
    # contiguos: fin de uno == inicio del siguiente
    for a, b in zip(segs, segs[1:]):
        assert a[1] == b[0]


def test_merge_min_absorbs_short() -> None:
    segs = [[0.0, 0.5], [0.5, 1.0], [1.0, 5.0]]
    out = _merge_min(segs, min_clip=1.5)
    # los dos cortos se funden hacia adelante
    assert out[0][0] == 0.0
    assert out[-1][1] == 5.0
    assert all((e - s) >= 1.5 for s, e in out)


def test_split_max_breaks_long_segment() -> None:
    out = _split_max([[0.0, 20.0]], max_clip=8.0, beats=None, snap=False)
    assert len(out) >= 3
    assert out[0][0] == 0.0
    assert out[-1][1] == 20.0
    assert all((e - s) <= 8.0 + 1e-6 for s, e in out)


def test_plan_segments_anchors_and_covers() -> None:
    lt = _timings([(1.0, 3.0), (3.0, 6.0), (6.0, 10.0), (10.0, 14.0)])
    segs = plan_segments_from_timings(lt, SHOTS, total_seconds=16.0, snap=False)
    assert segs, "debe producir segmentos"
    # cobertura total contigua de 0 a 16
    assert segs[0]["start_sec"] == 0.0
    assert abs(segs[-1]["end_sec"] - 16.0) < 0.01
    for a, b in zip(segs, segs[1:]):
        assert abs(a["end_sec"] - b["start_sec"]) < 0.01
    # cada segmento trae prompts y source musical
    assert all(s["source"] == "music" for s in segs)
    assert all("prompt_kling" in s for s in segs)
    # los shots asignados pertenecen al set
    slugs = {s["shot"]["slug"] for s in segs}
    assert slugs.issubset({"a", "b", "c"})


def test_plan_segments_snaps_to_beats() -> None:
    lt = _timings([(2.1, 4.0), (4.2, 8.0)])
    beats = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    segs = plan_segments_from_timings(
        lt, SHOTS, total_seconds=10.0, beats=beats, snap=True
    )
    cut_starts = [s["start_sec"] for s in segs]
    # el corte ~2.1 se ajusta a beat 2.0
    assert 2.0 in cut_starts


def test_high_energy_section_cuts_faster() -> None:
    lt = _timings([(0.0, 30.0)])  # una sola línea larga
    sections = [
        {"start_sec": 0.0, "end_sec": 30.0, "mean_energy": 0.9},  # alta
        {"start_sec": 0.0, "end_sec": 0.0, "mean_energy": 0.1},   # baja (referencia mediana)
    ]
    hi = plan_segments_from_timings(lt, SHOTS, total_seconds=30.0, sections=sections, snap=False)
    lo = plan_segments_from_timings(lt, SHOTS, total_seconds=30.0, snap=False)
    # con sección de alta energía debe trocear más (clips más cortos)
    assert len(hi) > len(lo)


def test_plan_timeline_falls_back_to_heuristic() -> None:
    segs, source = plan_timeline(SHOTS, line_timings=None, total_seconds=90.0)
    assert source == "heuristic"
    assert len(segs) == len(SHOTS)
    assert all(s.get("source") == "heuristic" for s in segs)


def test_plan_timeline_uses_music_when_timings() -> None:
    lt = _timings([(1.0, 4.0), (4.0, 8.0), (8.0, 12.0)])
    music = {"duration_sec": 14.0, "beats": [], "sections": []}
    segs, source = plan_timeline(SHOTS, line_timings=lt, music=music)
    assert source == "music"
    assert abs(segs[-1]["end_sec"] - 14.0) < 0.01
