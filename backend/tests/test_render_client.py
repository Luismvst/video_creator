"""Tests del cliente de render (v2-F3). Puros + dry-run: sin red ni FAL_KEY."""

import pytest

from app.render_client import (
    estimate_render_cost,
    provider_prompt,
    render_segment,
    render_timeline,
    within_budget,
)


def _segs(n, dur=6.0):
    return [
        {"index": i + 1, "duration_sec": dur,
         "prompt_generic": f"g{i}", "prompt_kling": f"k{i}", "prompt_runway": f"r{i}"}
        for i in range(n)
    ]


def test_estimate_cost_math_kling() -> None:
    est = estimate_render_cost(_segs(30, 6.0), provider="kling", reroll_factor=1.4)
    # 30*6 = 180s @ 0.10 = 18.0 ; con rerolls 1.4 = 25.2
    assert est["total_video_sec"] == 180.0
    assert est["subtotal_usd"] == 18.0
    assert est["estimated_usd"] == pytest.approx(25.2, abs=0.01)
    assert est["n_segments"] == 30


def test_estimate_cost_provider_rates_differ() -> None:
    segs = _segs(10, 6.0)
    wan = estimate_render_cost(segs, provider="wan", reroll_factor=1.0)["subtotal_usd"]
    kling = estimate_render_cost(segs, provider="kling", reroll_factor=1.0)["subtotal_usd"]
    veo = estimate_render_cost(segs, provider="veo3", reroll_factor=1.0)["subtotal_usd"]
    assert wan < kling < veo


def test_within_budget_gate() -> None:
    est = estimate_render_cost(_segs(30, 6.0), provider="kling")  # ~25.2
    ok, _ = within_budget(est, 40.0)
    assert ok
    bad, reason = within_budget(est, 10.0)
    assert not bad and "supera el tope" in reason
    # sin tope siempre pasa
    assert within_budget(est, None)[0]


def test_provider_prompt_selection() -> None:
    seg = {"prompt_generic": "g", "prompt_kling": "k", "prompt_runway": "r"}
    assert provider_prompt(seg, "kling") == "k"
    assert provider_prompt(seg, "runway") == "r"
    assert provider_prompt(seg, "veo3") == "g"
    # fallback a genérico si falta el campo del proveedor
    assert provider_prompt({"prompt_generic": "g"}, "kling") == "g"


def test_render_segment_dry_run_no_key() -> None:
    seg = _segs(1)[0]
    out = render_segment(seg, provider="kling", dry_run=True)
    assert out["ok"] and out["dry_run"]
    assert out["prompt_preview"] == "k0"
    assert out["would_write"].endswith("clip_001.mp4")


def test_render_timeline_dry_run_plan() -> None:
    res = render_timeline(_segs(5), provider="kling", dry_run=True)
    assert res["ok"] and res["dry_run"]
    assert res["rendered_ok"] == 5
    assert res["estimate"]["n_segments"] == 5


def test_render_timeline_aborts_over_budget() -> None:
    res = render_timeline(_segs(60, 8.0), provider="veo3", max_budget_usd=20.0, dry_run=True)
    # 60*8=480s @0.75 *1.4 = enorme → debe abortar antes de "gastar"
    assert res["ok"] is False
    assert res["aborted"] is True
    assert "estimate" in res


def test_render_timeline_limit() -> None:
    res = render_timeline(_segs(30), provider="kling", dry_run=True, limit=1)
    assert res["estimate"]["n_segments"] == 1
    assert len(res["segments"]) == 1


def test_render_timeline_real_without_key_errors() -> None:
    res = render_timeline(_segs(2), provider="kling", dry_run=False, fal_key=None)
    assert res["ok"] is False
    assert "FAL_KEY" in res["error"]
