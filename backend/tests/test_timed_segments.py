from app.timed_segments import propose_timed_segments
from app.video_cost_estimate import estimate_segment_costs_usd


def test_timed_segments_sum_to_total() -> None:
    shots = [
        {"slug": "a", "camera": "wide", "action": "open", "notes": "n1"},
        {"slug": "b", "camera": "close", "action": "detail", "notes": "n2"},
        {"slug": "c", "camera": "medium", "action": "bridge", "notes": "n3"},
    ]
    total = 180.0
    segs = propose_timed_segments(total, shots)
    assert len(segs) == 3
    assert abs(segs[-1]["end_sec"] - total) < 0.15
    s = sum(s["duration_sec"] for s in segs)
    assert abs(s - total) < 0.2
    for s in segs:
        assert "prompt_generic" in s
        assert "## 1." in s["prompt_generic"] or "open" in s["prompt_generic"].lower()


def test_cost_estimate_keys() -> None:
    segs = propose_timed_segments(60.0, [{"slug": "x", "camera": "c", "action": "a", "notes": "n"}])
    est = estimate_segment_costs_usd(segs)
    assert "totals_usd" in est
    assert set(est["totals_usd"].keys()) == {"generic", "runway", "kling"}
    assert est["totals_usd"]["generic"] >= 0
