from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.services.mock_draft_scenario_variant_service import SCENARIO_NAMES

DEFAULT_SCENARIO_VARIANT_ROOT = Path(
    "local_exports/mock_draft/scenario_variants_20260617"
)
DEFAULT_SCENARIO_COMPARISON_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/scenario_comparison_20260617"
)

TIM_AVAILABILITY_FILE = "tim_scenario_availability_rows.csv"
PICK_BY_PICK_FILE = "scenario_variant_pick_by_pick_review_rows.csv"

MATRIX_COLUMNS = (
    "pick_label",
    "overall_pick",
    "scenario_name",
    "tim_manual_review_only",
    "frozen_rookie_options",
    "value_neutral_options",
    "top_frozen_rookie_options",
    "top_value_neutral_options",
    "availability_label_policy",
)
ROOKIE_STABILITY_COLUMNS = (
    "pick_label",
    "asset_id",
    "player",
    "position",
    "rank",
    "tier",
    "draft_action",
    "warning_severity",
    "scenario_count_available",
    "scenario_count_total",
    "availability_label",
    "review_flags",
    "nwr_score_status",
    "stats_model_value",
)
VALUE_NEUTRAL_COLUMNS = (
    "pick_label",
    "scenario_name",
    "asset_id",
    "player",
    "position",
    "player_source",
    "value_status",
    "review_flags",
    "visibility_only_note",
    "stats_model_value",
)


@dataclass(frozen=True)
class ScenarioComparisonKit:
    review_only: bool
    matrix_rows: tuple[dict[str, object], ...]
    stable_rookie_rows: tuple[dict[str, object], ...]
    fragile_rookie_rows: tuple[dict[str, object], ...]
    value_neutral_rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def build_scenario_comparison_kit(
    *,
    scenario_root: str | Path = DEFAULT_SCENARIO_VARIANT_ROOT,
    availability_rows: Sequence[Mapping[str, object]] | None = None,
    pick_rows: Sequence[Mapping[str, object]] | None = None,
) -> ScenarioComparisonKit:
    root = Path(scenario_root)
    availability = tuple(
        dict(row)
        for row in (
            availability_rows
            if availability_rows is not None
            else _read_csv(root / TIM_AVAILABILITY_FILE)
        )
    )
    picks = tuple(
        dict(row)
        for row in (
            pick_rows
            if pick_rows is not None
            else _read_csv(root / PICK_BY_PICK_FILE)
        )
    )
    if not availability:
        raise FileNotFoundError("Scenario comparison requires Tim availability rows.")
    if not picks:
        raise FileNotFoundError("Scenario comparison requires pick-by-pick rows.")

    matrix_rows = _matrix_rows(availability, picks)
    stable_rows, fragile_rows = _rookie_stability_rows(availability)
    value_neutral_rows = _value_neutral_rows(availability)
    manifest = _manifest(
        availability_rows=availability,
        pick_rows=picks,
        matrix_rows=matrix_rows,
        stable_rookie_rows=stable_rows,
        fragile_rookie_rows=fragile_rows,
        value_neutral_rows=value_neutral_rows,
    )
    return ScenarioComparisonKit(
        review_only=True,
        matrix_rows=tuple(matrix_rows),
        stable_rookie_rows=tuple(stable_rows),
        fragile_rookie_rows=tuple(fragile_rows),
        value_neutral_rows=tuple(value_neutral_rows),
        manifest=manifest,
        artifact_paths={},
    )


def write_scenario_comparison_artifacts(
    kit: ScenarioComparisonKit,
    *,
    output_root: str | Path = DEFAULT_SCENARIO_COMPARISON_OUTPUT_ROOT,
) -> ScenarioComparisonKit:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    matrix_path = root / "tim_pick_window_scenario_matrix.csv"
    stable_path = root / "scenario_stable_rookie_options.csv"
    fragile_path = root / "scenario_fragile_rookie_options.csv"
    value_neutral_path = root / "scenario_value_neutral_visibility.csv"
    manifest_path = root / "scenario_comparison_manifest.json"
    _write_csv(matrix_path, MATRIX_COLUMNS, kit.matrix_rows)
    _write_csv(stable_path, ROOKIE_STABILITY_COLUMNS, kit.stable_rookie_rows)
    _write_csv(fragile_path, ROOKIE_STABILITY_COLUMNS, kit.fragile_rookie_rows)
    _write_csv(value_neutral_path, VALUE_NEUTRAL_COLUMNS, kit.value_neutral_rows)
    manifest = {
        **kit.manifest,
        "artifact_paths": {
            "scenario_matrix": str(matrix_path),
            "stable_rookies": str(stable_path),
            "fragile_rookies": str(fragile_path),
            "value_neutral_visibility": str(value_neutral_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return ScenarioComparisonKit(
        review_only=kit.review_only,
        matrix_rows=kit.matrix_rows,
        stable_rookie_rows=kit.stable_rookie_rows,
        fragile_rookie_rows=kit.fragile_rookie_rows,
        value_neutral_rows=kit.value_neutral_rows,
        manifest=manifest,
        artifact_paths={
            "scenario_matrix": matrix_path,
            "stable_rookies": stable_path,
            "fragile_rookies": fragile_path,
            "value_neutral_visibility": value_neutral_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_scenario_comparison_artifacts(
    *,
    scenario_root: str | Path = DEFAULT_SCENARIO_VARIANT_ROOT,
    output_root: str | Path = DEFAULT_SCENARIO_COMPARISON_OUTPUT_ROOT,
) -> ScenarioComparisonKit:
    return write_scenario_comparison_artifacts(
        build_scenario_comparison_kit(scenario_root=scenario_root),
        output_root=output_root,
    )


def _matrix_rows(
    availability: Sequence[Mapping[str, object]],
    picks: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    tim_picks = {
        (str(row.get("pick_label") or ""), str(row.get("scenario_name") or ""))
        for row in picks
        if row.get("selection_mode") == "Tim_review_pick"
    }
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in availability:
        grouped[(str(row.get("pick_label") or ""), str(row.get("scenario_name") or ""))].append(
            row
        )
    rows: list[dict[str, object]] = []
    for (pick_label, scenario_name), group in sorted(grouped.items()):
        frozen = [row for row in group if row.get("player_source") == "frozen_rookie"]
        value_neutral = [
            row for row in group if row.get("value_status") == "value_neutral"
        ]
        rows.append(
            {
                "pick_label": pick_label,
                "overall_pick": group[0].get("overall_pick") or "",
                "scenario_name": scenario_name,
                "tim_manual_review_only": (pick_label, scenario_name) in tim_picks,
                "frozen_rookie_options": len(frozen),
                "value_neutral_options": len(value_neutral),
                "top_frozen_rookie_options": _join_names(frozen[:5]),
                "top_value_neutral_options": _join_names(value_neutral[:5]),
                "availability_label_policy": (
                    "stable/fragile labels describe scenario availability only, "
                    "not NWR quality or rank."
                ),
            }
        )
    return rows


def _rookie_stability_rows(
    availability: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scenario_total = len({str(row.get("scenario_name") or "") for row in availability})
    by_pick_asset: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in availability:
        if row.get("player_source") == "frozen_rookie":
            key = (str(row.get("pick_label") or ""), str(row.get("asset_id") or ""))
            by_pick_asset[key].append(row)
    stable: list[dict[str, object]] = []
    fragile: list[dict[str, object]] = []
    for (pick_label, asset_id), rows in sorted(by_pick_asset.items()):
        first = rows[0]
        scenario_count = len({str(row.get("scenario_name") or "") for row in rows})
        payload = {
            "pick_label": pick_label,
            "asset_id": asset_id,
            "player": first.get("player") or "",
            "position": first.get("position") or "",
            "rank": first.get("rank") or "",
            "tier": first.get("tier") or "",
            "draft_action": first.get("draft_action") or "",
            "warning_severity": first.get("warning_severity") or "",
            "scenario_count_available": scenario_count,
            "scenario_count_total": scenario_total,
            "availability_label": (
                "stable_available_all_scenarios"
                if scenario_count == scenario_total
                else "fragile_available_some_scenarios"
            ),
            "review_flags": first.get("review_flags") or "",
            "nwr_score_status": first.get("nwr_score_status") or "",
            "stats_model_value": first.get("stats_model_value", 0.0),
        }
        if scenario_count == scenario_total:
            stable.append(payload)
        else:
            fragile.append(payload)
    return stable, fragile


def _value_neutral_rows(
    availability: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in availability:
        if row.get("value_status") != "value_neutral":
            continue
        rows.append(
            {
                "pick_label": row.get("pick_label") or "",
                "scenario_name": row.get("scenario_name") or "",
                "asset_id": row.get("asset_id") or "",
                "player": row.get("player") or "",
                "position": row.get("position") or "",
                "player_source": row.get("player_source") or "",
                "value_status": row.get("value_status") or "",
                "review_flags": row.get("review_flags") or "",
                "visibility_only_note": (
                    "Value-neutral visibility only; not ranked against rookies as "
                    "NWR quality."
                ),
                "stats_model_value": row.get("stats_model_value", 0.0),
            }
        )
    return rows


def _manifest(
    *,
    availability_rows: Sequence[Mapping[str, object]],
    pick_rows: Sequence[Mapping[str, object]],
    matrix_rows: Sequence[Mapping[str, object]],
    stable_rookie_rows: Sequence[Mapping[str, object]],
    fragile_rookie_rows: Sequence[Mapping[str, object]],
    value_neutral_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    flags: Counter[str] = Counter()
    for row in value_neutral_rows:
        for flag in str(row.get("review_flags") or "").split("|"):
            if flag:
                flags[flag] += 1
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "source_artifacts": {
            "tim_availability": str(DEFAULT_SCENARIO_VARIANT_ROOT / TIM_AVAILABILITY_FILE),
            "pick_by_pick": str(DEFAULT_SCENARIO_VARIANT_ROOT / PICK_BY_PICK_FILE),
        },
        "scenario_names": sorted(
            {str(row.get("scenario_name") or "") for row in availability_rows}
        ),
        "expected_scenario_names": list(SCENARIO_NAMES),
        "tim_availability_input_rows": len(availability_rows),
        "pick_by_pick_input_rows": len(pick_rows),
        "matrix_rows": len(matrix_rows),
        "stable_rookie_rows": len(stable_rookie_rows),
        "fragile_rookie_rows": len(fragile_rookie_rows),
        "value_neutral_visibility_rows": len(value_neutral_rows),
        "review_flags": dict(sorted(flags.items())),
        "availability_label_policy": (
            "Stable and fragile labels describe whether a rookie is visible in "
            "Tim/Niners windows across scenarios; they are not NWR quality labels."
        ),
        "nwr_score_policy": (
            "Scenario comparison does not invent numeric NWR scores or use market "
            "timing as rookie guidance."
        ),
        "tim_pick_policy": (
            "Tim/Niners picks remain manual-review only; no best pick is auto-finalized."
        ),
        "value_neutral_policy": (
            "Value-neutral veterans/free agents are visibility-only and are not "
            "ranked against frozen rookies as NWR quality."
        ),
        "promotion_status": "local_review_output_only_not_app_wired_not_promoted",
    }


def _join_names(rows: Sequence[Mapping[str, object]]) -> str:
    return " | ".join(str(row.get("player") or "") for row in rows if row.get("player"))


def _read_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: Sequence[Mapping[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
