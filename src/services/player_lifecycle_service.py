from __future__ import annotations

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIFECYCLE_SOURCE_ROOT = (
    PROJECT_ROOT / "local_exports" / "active_veteran_model_public_sources"
)
STATS_FIRST_OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"

INCOMING_ROOKIE = "incoming_rookie"
YOUNG_NFL_BRIDGE = "young_nfl_bridge"
YEAR_ONE_NFL_BRIDGE = "year_one_nfl_bridge"
YEAR_TWO_NFL_BRIDGE = "year_two_nfl_bridge"
YEAR_THREE_NFL_BRIDGE = "year_three_nfl_bridge"
ESTABLISHED_VETERAN = "established_veteran"
FREE_AGENT = "free_agent"
RELEASED_VETERAN = "released_veteran"

YOUNG_NFL_BRIDGE_LIFECYCLES = {
    YOUNG_NFL_BRIDGE,
    YEAR_ONE_NFL_BRIDGE,
    YEAR_TWO_NFL_BRIDGE,
    YEAR_THREE_NFL_BRIDGE,
}

LIFECYCLE_LABELS = {
    INCOMING_ROOKIE: "Incoming Rookie",
    YOUNG_NFL_BRIDGE: "Young NFL Bridge",
    YEAR_ONE_NFL_BRIDGE: "Year-One NFL Bridge",
    YEAR_TWO_NFL_BRIDGE: "Year-Two NFL Bridge",
    YEAR_THREE_NFL_BRIDGE: "Year-Three NFL Bridge",
    ESTABLISHED_VETERAN: "Established Veteran",
    FREE_AGENT: "Free Agent",
    RELEASED_VETERAN: "Released Veteran",
}


def asset_lifecycle_for_row(row: dict[str, object]) -> str:
    explicit = str(row.get("asset_lifecycle") or "").strip()
    if explicit in LIFECYCLE_LABELS:
        return explicit

    asset_type = str(row.get("asset_type") or row.get("asset_type_label") or "").lower()
    if "rookie" in asset_type:
        return INCOMING_ROOKIE
    if "released" in asset_type:
        return RELEASED_VETERAN
    if "free_agent" in asset_type or "free agent" in asset_type:
        return FREE_AGENT

    experience_bucket = str(row.get("experience_bucket") or "").strip()
    bridge_weight = _float(row.get("young_nfl_bridge_weight"), 0.0)
    if experience_bucket == "year_one_nfl_player":
        return YEAR_ONE_NFL_BRIDGE
    if experience_bucket == "year_two_nfl_player":
        return YEAR_TWO_NFL_BRIDGE
    if experience_bucket == "year_three_nfl_player":
        return YEAR_THREE_NFL_BRIDGE
    if bridge_weight > 0:
        return YOUNG_NFL_BRIDGE
    if experience_bucket == "true_rookie":
        return INCOMING_ROOKIE
    return ESTABLISHED_VETERAN


def is_young_nfl_bridge_lifecycle(lifecycle: object) -> bool:
    return str(lifecycle or "") in YOUNG_NFL_BRIDGE_LIFECYCLES


def asset_lifecycle_label(lifecycle: object) -> str:
    return LIFECYCLE_LABELS.get(str(lifecycle or ""), "Established Veteran")


def add_lifecycle_fields(row: dict[str, object]) -> dict[str, object]:
    updated = dict(row)
    lifecycle = asset_lifecycle_for_row(updated)
    updated["asset_lifecycle"] = lifecycle
    updated["asset_lifecycle_label"] = asset_lifecycle_label(lifecycle)
    return updated


def load_active_lifecycle_lookup(
    source_root: str | Path = DEFAULT_LIFECYCLE_SOURCE_ROOT,
) -> dict[str, dict[str, object]]:
    output_path = Path(source_root) / STATS_FIRST_OUTPUT_FILE
    if not output_path.exists():
        return {}
    rows = _read_csv(output_path)
    output: dict[str, dict[str, object]] = {}
    for row in rows:
        enriched = add_lifecycle_fields(row)
        for key in _candidate_keys(enriched):
            output.setdefault(key, enriched)
    return output


def lifecycle_from_lookup(
    row: dict[str, object],
    lookup: dict[str, dict[str, object]],
) -> dict[str, object]:
    updated = dict(row)
    match = next((lookup[key] for key in _candidate_keys(row) if key in lookup), {})
    for field in (
        "experience_bucket",
        "young_nfl_bridge_prior_score",
        "young_nfl_bridge_weight",
        "young_nfl_bridge_source",
    ):
        if field not in updated or updated.get(field) in (None, ""):
            updated[field] = match.get(field, "")
    return add_lifecycle_fields(updated)


def _candidate_keys(row: dict[str, object]) -> tuple[str, ...]:
    keys: list[str] = []
    for field in ("player_id", "sleeper_id", "gsis_id"):
        value = str(row.get(field) or "")
        if value:
            keys.append(f"{field}:{value}")
    name = _clean_name(str(row.get("player_name") or row.get("player") or ""))
    position = str(row.get("position") or row.get("pos") or "")
    if name and position:
        keys.append(f"name_position:{name}|{position}")
    return tuple(keys)


def _clean_name(value: str) -> str:
    lowered = value.lower().strip()
    for suffix in (" jr.", " sr.", " iii", " ii", " iv"):
        lowered = lowered.replace(suffix, "")
    return " ".join(lowered.replace(".", "").split())


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
