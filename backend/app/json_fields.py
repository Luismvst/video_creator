import json
from typing import Any

from fastapi import HTTPException

_JSON_PATCH_KEYS = frozenset(
    {
        "line_timings_json",
        "creative_intake_json",
        "director_answers_json",
        "creative_routes_json",
        "creative_lock_snapshot_json",
        "timeline_plan_json",
        "scenes_json",
        "shots_json",
        "generation_plan_json",
        "review_matrix_json",
    }
)


def validate_json_blob(key: str, value: Any) -> None:
    if key not in _JSON_PATCH_KEYS:
        return
    if value is None or value == "":
        return
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"{key} must be a JSON string")
    try:
        json.loads(value)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in {key}: {e}") from e


def parse_json_optional(raw: str | None, default: Any) -> Any:
    if not raw or not str(raw).strip():
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default
