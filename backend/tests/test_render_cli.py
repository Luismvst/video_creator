"""CLI de render: dry-run por defecto y gate de presupuesto."""

import json

from app.render_cli import main

SEGMENTS = [
    {"index": 1, "duration_sec": 4.0, "prompt_kling": "k1", "prompt_generic": "g1"},
    {"index": 2, "duration_sec": 4.0, "prompt_kling": "k2", "prompt_generic": "g2"},
]


def _write(tmp_path, data):
    p = tmp_path / "segments.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_cli_dry_run_ok(tmp_path) -> None:
    code = main(["--segments", _write(tmp_path, SEGMENTS), "--provider", "kling"])
    assert code == 0


def test_cli_budget_gate_aborts(tmp_path) -> None:
    # 8s @ $0.75/s × 1.4 = $8.4 > tope $1 → aborta con código 2.
    code = main(["--segments", _write(tmp_path, SEGMENTS), "--provider", "veo3", "--max-budget", "1"])
    assert code == 2


def test_cli_accepts_wrapped_segments(tmp_path) -> None:
    code = main(["--segments", _write(tmp_path, {"segments": SEGMENTS}), "--provider", "wan"])
    assert code == 0


def test_cli_missing_file() -> None:
    assert main(["--segments", "no_existe_segments.json"]) == 1
