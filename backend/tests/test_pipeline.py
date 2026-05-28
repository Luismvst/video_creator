"""Tests de F4 (keyframes) y del orquestador E2E (dry-run, sin keys ni binarios)."""

from app.keyframes import estimate_keyframe_cost, keyframe_prompt, plan_keyframes
from app.pipeline import run_pipeline

LYRICS = "Caía la nieve sobre el puerto\ny nadie hablaba\n\nvolví a buscarte\nen la marea"


def _segs(n):
    return [
        {"index": i + 1, "duration_sec": 6.0,
         "shot": {"action": f"accion {i}", "camera": "plano medio", "notes": "frio"},
         "prompt_generic": f"g{i}", "prompt_kling": f"k{i}"}
        for i in range(n)
    ]


def test_keyframe_prompt_from_shot() -> None:
    seg = {"shot": {"action": "puerto nevado", "camera": "gran angular", "notes": "frio"}}
    pr = keyframe_prompt(seg)
    assert "puerto nevado" in pr and "gran angular" in pr
    # fallback al genérico si no hay shot
    assert keyframe_prompt({"prompt_generic": "gen"}) == "gen"


def test_estimate_keyframe_cost() -> None:
    est = estimate_keyframe_cost(10, usd_per_image=0.04)
    assert est["n_images"] == 10
    assert est["estimated_usd"] == 0.4


def test_plan_keyframes_chains_references() -> None:
    plan = plan_keyframes(_segs(3), chain=True, dry_run=True)
    kfs = plan["keyframes"]
    assert plan["dry_run"] is True
    assert len(kfs) == 3
    # el primero no tiene referencia; los siguientes referencian el anterior
    assert kfs[0]["reference_image"] is None
    assert kfs[1]["reference_image"] == kfs[0]["would_write"]
    assert kfs[2]["reference_image"] == kfs[1]["would_write"]
    assert plan["estimate"]["n_images"] == 3


def test_plan_keyframes_no_chain() -> None:
    plan = plan_keyframes(_segs(2), chain=False, dry_run=True)
    assert all(k["reference_image"] is None for k in plan["keyframes"])


def test_pipeline_lyrics_only_dry_run(tmp_path) -> None:
    m = run_pipeline(
        lyrics_text=LYRICS, target_duration=120.0, provider="kling",
        max_budget_usd=40.0, dry_run=True, work_dir=str(tmp_path / "vz"),
    )
    assert m["dry_run"] is True
    # sin audio → fuente heurística y audio degradado
    assert m["timeline_source"] == "heuristic"
    assert m["n_segments"] >= 1
    assert m["duration_sec"] == 120.0
    assert m["cost"]["render_usd"] is not None
    assert m["cost"]["over_budget"] is False
    # ensamblado bloqueado (sin clips ni audio real), pero con comando construido
    assert m["f5_assembly"]["command"][0] == "ffmpeg"


def test_pipeline_budget_abort_surfaces(tmp_path) -> None:
    m = run_pipeline(
        lyrics_text=LYRICS, target_duration=600.0, provider="veo3",
        max_budget_usd=5.0, dry_run=True, work_dir=str(tmp_path / "vz"),
    )
    assert m["cost"]["over_budget"] is True
    assert m["f3_render"]["aborted"] is True


def test_pipeline_keyframes_cost_added(tmp_path) -> None:
    m = run_pipeline(
        lyrics_text=LYRICS, target_duration=60.0, provider="kling",
        keyframes=True, dry_run=True, work_dir=str(tmp_path / "vz"),
    )
    assert m["f4_keyframes"] is not None
    assert m["f4_keyframes"]["planned"] == m["n_segments"]
    # total = render + keyframes
    rc = m["cost"]
    assert rc["keyframes_usd"] is not None
    assert rc["total_estimated_usd"] >= rc["render_usd"]
