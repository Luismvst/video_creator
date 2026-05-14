"""API smoke tests (isolated SQLite file)."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name.replace(os.sep, "/")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    init_db()
    with TestClient(app) as c:
        yield c


def test_creative_lock_unlock(client: TestClient) -> None:
    r = client.post("/projects", json={"name": "pytest"})
    assert r.status_code == 200
    pid = r.json()["id"]
    r2 = client.patch(
        f"/projects/{pid}/song",
        json={
            "lyrics_text": "uno\ndos",
            "lyrics_rights_confirmed": True,
        },
    )
    assert r2.status_code == 200
    lock = client.post(f"/projects/{pid}/creative/lock")
    assert lock.status_code == 200
    body = lock.json()
    assert body["song"]["creative_locked"] is True
    assert body["song"]["creative_lock_snapshot_json"]

    bad = client.patch(f"/projects/{pid}/song", json={"lyrics_text": "tres"})
    assert bad.status_code == 400

    ul = client.post(f"/projects/{pid}/creative/unlock")
    assert ul.status_code == 200
    assert ul.json()["song"]["creative_locked"] is False


def test_enqueue_stub_recommendations(client: TestClient) -> None:
    r = client.post("/projects", json={"name": "enqueue"})
    pid = r.json()["id"]
    client.patch(
        f"/projects/{pid}/song",
        json={"lyrics_text": "a\nb", "lyrics_rights_confirmed": True},
    )
    q = client.post(f"/projects/{pid}/analysis/enqueue")
    assert q.status_code == 200
    body = q.json()
    assert body["status"] == "accepted_stub"
    assert isinstance(body.get("recommendations"), list)
    assert len(body["recommendations"]) >= 2


def test_export_shots_json_csv(client: TestClient) -> None:
    r = client.post("/projects", json={"name": "shots"})
    pid = r.json()["id"]
    shots = [{"slug": "s1", "camera": "wide", "action": "walk", "notes": "continuity"}]
    client.patch(f"/projects/{pid}/song", json={"shots_json": json.dumps(shots)})
    jr = client.get(f"/projects/{pid}/export/shots.json")
    assert jr.status_code == 200
    assert jr.json()[0]["slug"] == "s1"
    cr = client.get(f"/projects/{pid}/export/shots.csv")
    assert cr.status_code == 200
    assert "slug" in cr.text
    assert "wide" in cr.text


def test_documents_preview(client: TestClient) -> None:
    r = client.post("/projects", json={"name": "docprev"})
    pid = r.json()["id"]
    pr = client.get(f"/projects/{pid}/documents/preview")
    assert pr.status_code == 200
    data = pr.json()
    assert "visual_bible_markdown" in data
    assert "treatment_markdown" in data
    assert "Visual Bible" in data["visual_bible_markdown"]


def test_uat_neon_urban_breakup_journey(client: TestClient) -> None:
    """End-to-end API walkthrough for docs/UAT-NEON-URBAN-BREAKUP.md (neon urban breakup)."""
    lyrics = (
        "Neón en el retrovisor\n"
        "Fantasmas de domingo\n"
        "Callamos como el asfalto\n"
        "Cuando ya no queda historia"
    )
    r = client.post("/projects", json={"name": "UAT Neón urbano"})
    assert r.status_code == 200
    pid = r.json()["id"]

    up = client.patch(
        f"/projects/{pid}/song",
        json={
            "title": "Domingo de neón",
            "artist": "UAT Ficticio",
            "mood": "melancólico, urbano, nocturno",
            "target_duration_seconds": 180,
            "pacing_profile": "slow_cinematic",
            "lyrics_text": lyrics,
            "lyrics_rights_confirmed": True,
        },
    )
    assert up.status_code == 200

    s1 = client.post(
        f"/projects/{pid}/song/sections",
        json={"label": "Apertura", "kind": "verse", "start_line_index": 0, "end_line_index": 1},
    )
    assert s1.status_code == 200
    s2 = client.post(
        f"/projects/{pid}/song/sections",
        json={"label": "Cierre", "kind": "chorus", "start_line_index": 2, "end_line_index": 3},
    )
    assert s2.status_code == 200

    gen = client.post(
        f"/projects/{pid}/song/insights/generate",
        json={"mode": "heuristic", "replace": True},
    )
    assert gen.status_code == 200
    assert gen.json().get("created_count", 0) >= 1

    intake = {
        "reference_notes": "Ciudad húmeda, neón; sin nombres de obras reales.",
        "style_attributes": ["neón frío", "cámara estable"],
    }
    director = {
        "visual_density": "media",
        "color_bible": "fría neón + sombras",
        "protagonist_energy": "contenida",
        "ending_tone": "melancólica",
        "camera_language": "plano secuencia suave",
    }
    routes = {
        "routes": [
            {"id": "route-intimate", "title": "Ruta A — coche", "summary": "Espacio reducido; neón como acento."},
            {"id": "route-walk", "title": "Ruta B — túnel", "summary": "Exterior; montaje más fragmentado."},
        ],
    }
    shots = [
        {
            "slug": "retrovisor",
            "camera": "primer plano retrovisor",
            "action": "mirada fija; neón en el cristal",
            "notes": "paleta intake",
        },
        {
            "slug": "asfalto",
            "camera": "detalle charco",
            "action": "caminata lenta",
            "notes": "transición desde interior",
        },
    ]
    plan = [
        {"title": "Moodboard interno", "detail": "Atributos ya en intake."},
        {"title": "Generación externa", "detail": "Runway/Kling con exports."},
    ]

    pj = client.patch(
        f"/projects/{pid}/song",
        json={
            "creative_intake_json": json.dumps(intake, ensure_ascii=False),
            "director_answers_json": json.dumps(director, ensure_ascii=False),
            "creative_routes_json": json.dumps(routes, ensure_ascii=False),
            "selected_route_id": "route-intimate",
            "shots_json": json.dumps(shots, ensure_ascii=False),
            "generation_plan_json": json.dumps(plan, ensure_ascii=False),
        },
    )
    assert pj.status_code == 200
    assert not (pj.json()["song"].get("structure_warnings") or [])

    pr = client.get(f"/projects/{pid}/documents/preview")
    assert pr.status_code == 200
    vb = pr.json()["visual_bible_markdown"]
    assert "Neón" in vb or "Apertura" in vb
    assert "Ruta A" in pr.json()["treatment_markdown"]

    q = client.post(f"/projects/{pid}/analysis/enqueue")
    assert q.status_code == 200
    body = q.json()
    assert body["status"] == "accepted_stub"
    assert isinstance(body.get("recommendations"), list)

    lock = client.post(f"/projects/{pid}/creative/lock")
    assert lock.status_code == 200
    assert lock.json()["song"]["creative_locked"] is True

    pr2 = client.get(f"/projects/{pid}/documents/preview")
    assert pr2.status_code == 200
    assert "Visual Bible" in pr2.json()["visual_bible_markdown"]

    bad = client.patch(f"/projects/{pid}/song", json={"lyrics_text": "cambio prohibido"})
    assert bad.status_code == 400

    bundle = client.get(f"/projects/{pid}/export/bundle.md")
    assert bundle.status_code == 200
    assert "Visual Bible" in bundle.text
    assert "retrovisor" in bundle.text

    sj = client.get(f"/projects/{pid}/export/shots.json")
    assert sj.status_code == 200
    assert len(sj.json()) == 2

    ul = client.post(f"/projects/{pid}/creative/unlock")
    assert ul.status_code == 200
    assert ul.json()["song"]["creative_locked"] is False
