from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_formula_contract_service import (
    NFL_MATRIX,
    REPLACEMENT_VORP_PLAYER_ROWS,
    assert_formula_field_allowed,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_11C_RB_WR_CURRENT_VALUE.md")

RB_WR_CURRENT_VALUE_VERSION = "model_v4_phase_11c_rb_wr_current_value_0.1.0"
SUPPORTED_POSITIONS = ("RB", "WR")

COMPONENT_WEIGHTS = {
    "RB": {
        "vorp_anchor": 0.45,
        "role_volume": 0.25,
        "first_down_high_value": 0.15,
        "receiving_utility": 0.10,
        "efficiency_context": 0.05,
    },
    "WR": {
        "vorp_anchor": 0.40,
        "target_route_role": 0.30,
        "first_down_yardage": 0.15,
        "air_yard_role": 0.10,
        "efficiency_context": 0.05,
    },
}

VALUE_HEADER = (
    "canonical_player_key",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "scoring_season",
    "current_value_review_score",
    "confidence_multiplier",
    "confidence_status",
    "available_component_weight",
    "vorp_anchor_score",
    "role_volume_score",
    "target_route_role_score",
    "first_down_high_value_score",
    "first_down_yardage_score",
    "receiving_utility_score",
    "air_yard_role_score",
    "efficiency_context_score",
    "positive_vorp_points",
    "review_scoring_points",
    "imported_first_down_points",
    "first_down_source_status",
    "return_source_status",
    "allowed_use",
    "warning_flags",
    "formula_version",
)

COMPONENT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "component_name",
    "raw_component_value",
    "normalized_score",
    "component_weight",
    "weighted_contribution",
    "source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_pointer",
    "component_warning",
    "formula_version",
)

RECEIPT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "feature_group",
    "receipt_pointer",
    "source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_requirement",
    "formula_version",
)

WARNING_HEADER = (
    "entity_key",
    "player_name",
    "position",
    "warning_type",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)


@dataclass(frozen=True)
class RbWrCurrentValueResult:
    value_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class RbWrCurrentValuePaths:
    value_rows: Path
    component_rows: Path
    receipts: Path
    warnings: Path
    doc: Path


@dataclass(frozen=True)
class _Component:
    name: str
    raw_value: float | None
    normalized_score: float | None
    weight: float
    source_status: str
    allowed_input_file: str
    allowed_lane: str
    allowed_field_or_json_path: str
    receipt_pointer: str
    warning: str = ""

    @property
    def weighted_contribution(self) -> float | None:
        if self.normalized_score is None:
            return None
        return round(self.normalized_score * self.weight, 4)


def build_rb_wr_current_value(
    *,
    nfl_matrix_path: str | Path = NFL_MATRIX,
    vorp_rows_path: str | Path = REPLACEMENT_VORP_PLAYER_ROWS,
) -> RbWrCurrentValueResult:
    _assert_phase_11c_contract()
    nfl_rows = _read_rows(Path(nfl_matrix_path))
    vorp_rows = _vorp_index(Path(vorp_rows_path))
    position_max_vorp = _position_max_vorp(vorp_rows)
    position_max_first_down = _position_max_first_down(vorp_rows)

    value_rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    for row in nfl_rows:
        position = str(row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        player = _score_row(
            row,
            vorp_rows.get(str(row.get("canonical_player_key") or "")),
            max_vorp=position_max_vorp.get(position, 0.0),
            max_first_down=position_max_first_down.get(position, 0.0),
        )
        value_rows.append(player["value_row"])
        component_rows.extend(player["component_rows"])
        receipt_rows.extend(player["receipt_rows"])
        warning_rows.extend(player["warning_rows"])

    value_rows.sort(
        key=lambda item: (
            -_float(item.get("current_value_review_score"), -1.0),
            str(item.get("position") or ""),
            str(item.get("player_name") or ""),
        )
    )
    warning_rows.extend(_sanity_warnings(value_rows))
    summary = {
        "formula_version": RB_WR_CURRENT_VALUE_VERSION,
        "review_status": "review_only",
        "player_rows": len(value_rows),
        "component_rows": len(component_rows),
        "receipt_rows": len(receipt_rows),
        "warning_rows": len(warning_rows),
        "market_rows_used": 0,
        "projection_rows_used": 0,
        "adp_rows_used": 0,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return RbWrCurrentValueResult(
        value_rows=tuple(value_rows),
        component_rows=tuple(component_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary=summary,
    )


def write_rb_wr_current_value_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: RbWrCurrentValueResult | None = None,
) -> RbWrCurrentValuePaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rb_wr_current_value()
    paths = RbWrCurrentValuePaths(
        value_rows=output / "rb_wr_current_value_review_rows.csv",
        component_rows=output / "rb_wr_current_value_component_rows.csv",
        receipts=output / "rb_wr_current_value_receipts.csv",
        warnings=output / "rb_wr_current_value_warnings.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.value_rows, VALUE_HEADER, result.value_rows)
    _write_csv(paths.component_rows, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_doc(paths.doc, result, paths)
    return paths


def _assert_phase_11c_contract() -> None:
    for module in ("rb_current_value", "wr_current_value"):
        for lane, path in (
            ("row_metadata", "position"),
            ("factual_evidence_json", "rotowire_player_stats"),
            ("derived_evidence_json", "rotowire_role_usage"),
            ("derived_evidence_json", "stats_first_component_evidence"),
        ):
            assert_formula_field_allowed(
                module_name=module,
                allowed_input_file=NFL_MATRIX,
                allowed_lane=lane,
                allowed_field_or_json_path=path,
            )
        assert_formula_field_allowed(
            module_name=module,
            allowed_input_file=REPLACEMENT_VORP_PLAYER_ROWS,
            allowed_lane="replacement_vorp_review",
            allowed_field_or_json_path=(
                "vorp_points|positive_vorp_points|review_scoring_points|"
                "imported_rushing_first_downs|imported_receiving_first_downs|"
                "imported_first_down_points|first_down_source_status|return_source_status"
            ),
        )


def _score_row(
    row: dict[str, str],
    vorp_row: dict[str, str] | None,
    *,
    max_vorp: float,
    max_first_down: float,
) -> dict[str, object]:
    position = str(row.get("position") or "")
    components = (
        _rb_components(row, vorp_row, max_vorp, max_first_down)
        if position == "RB"
        else _wr_components(row, vorp_row, max_vorp, max_first_down)
    )
    available_weight = round(
        sum(component.weight for component in components if component.normalized_score is not None),
        4,
    )
    weighted_sum = sum(
        component.weighted_contribution or 0.0
        for component in components
        if component.normalized_score is not None
    )
    raw_score = weighted_sum / available_weight if available_weight else None
    confidence, confidence_status, confidence_warnings = _confidence(components, row, vorp_row)
    final_score = round(raw_score * confidence, 4) if raw_score is not None else ""
    key = str(row.get("canonical_player_key") or "")
    player_name = str(row.get("player_name") or "")
    warning_flags = tuple(
        flag
        for flag in (
            _warning_flag_list(row.get("warning_flags"))
            + [component.warning for component in components if component.warning]
            + list(confidence_warnings)
        )
        if flag and flag != "review_only_vorp_context_excluded_from_private_value"
    )
    component_lookup = {component.name: component for component in components}
    value_row = {
        "canonical_player_key": key,
        "player_name": player_name,
        "normalized_player_name": row.get("normalized_player_name", ""),
        "position": position,
        "nfl_team": row.get("nfl_team", ""),
        "scoring_season": (vorp_row or {}).get("scoring_season", ""),
        "current_value_review_score": final_score,
        "confidence_multiplier": confidence,
        "confidence_status": confidence_status,
        "available_component_weight": available_weight,
        "vorp_anchor_score": _score_cell(component_lookup, "vorp_anchor"),
        "role_volume_score": _score_cell(component_lookup, "role_volume"),
        "target_route_role_score": _score_cell(component_lookup, "target_route_role"),
        "first_down_high_value_score": _score_cell(component_lookup, "first_down_high_value"),
        "first_down_yardage_score": _score_cell(component_lookup, "first_down_yardage"),
        "receiving_utility_score": _score_cell(component_lookup, "receiving_utility"),
        "air_yard_role_score": _score_cell(component_lookup, "air_yard_role"),
        "efficiency_context_score": _score_cell(component_lookup, "efficiency_context"),
        "positive_vorp_points": (vorp_row or {}).get("positive_vorp_points", ""),
        "review_scoring_points": (vorp_row or {}).get("review_scoring_points", ""),
        "imported_first_down_points": (vorp_row or {}).get("imported_first_down_points", ""),
        "first_down_source_status": (vorp_row or {}).get(
            "first_down_source_status", "missing_vorp_row"
        ),
        "return_source_status": (vorp_row or {}).get("return_source_status", "missing_vorp_row"),
        "allowed_use": "review_only_rb_wr_current_value",
        "warning_flags": "|".join(dict.fromkeys(warning_flags)),
        "formula_version": RB_WR_CURRENT_VALUE_VERSION,
    }
    component_rows = tuple(
        _component_row(key, player_name, position, component)
        for component in components
    )
    receipt_rows = _receipt_rows(key, player_name, position, row, vorp_row)
    warning_rows = _warning_rows(key, player_name, position, warning_flags)
    return {
        "value_row": value_row,
        "component_rows": component_rows,
        "receipt_rows": receipt_rows,
        "warning_rows": warning_rows,
    }


def _rb_components(
    row: dict[str, str],
    vorp_row: dict[str, str] | None,
    max_vorp: float,
    max_first_down: float,
) -> tuple[_Component, ...]:
    stats = _json(row.get("factual_evidence_json")).get("rotowire_player_stats", {})
    derived = _json(row.get("derived_evidence_json"))
    stats_first = derived.get("stats_first_component_evidence", {})
    role_usage = derived.get("rotowire_role_usage", {})
    weights = COMPONENT_WEIGHTS["RB"]
    return (
        _vorp_component(vorp_row, max_vorp, weights["vorp_anchor"]),
        _component(
            "role_volume",
            _average_present(
                _stats_first_score(stats_first, "target_carry_volume"),
                _stats_first_score(stats_first, "target_share_team_share"),
                _normalize(_metric(role_usage, "snaps", "snap_count_off_2"), 85.0),
            ),
            weights["role_volume"],
            "target_carry_volume|target_share_team_share|snap_count_off_2",
            "stats_first_historical_evidence|imported_snap_data",
            warning="missing_role_volume_evidence",
        ),
        _component(
            "first_down_high_value",
            _average_present(
                _first_down_score(vorp_row, max_first_down),
                _stats_first_score(stats_first, "red_zone_involvement"),
            ),
            weights["first_down_high_value"],
            "imported_first_down_points|red_zone_involvement",
            "imported_real_data|stats_first_historical_evidence",
            lane="replacement_vorp_review",
            warning="missing_first_down_high_value_evidence",
        ),
        _component(
            "receiving_utility",
            _average_present(
                _normalize(_stat(stats, "receiving:advanced", "receiving_tar"), 100.0),
                _normalize(_stat(stats, "receiving:advanced", "routes_run_tprr"), 25.0),
                _normalize(_stat(stats, "receiving:advanced", "routes_run_yprr"), 2.2),
                _normalize(_stat(stats, "receiving:advanced", "receiving_yds"), 700.0),
            ),
            weights["receiving_utility"],
            "receiving_tar|routes_run_tprr|routes_run_yprr|receiving_yds",
            "imported_real_data",
            lane="factual_evidence_json",
            warning="missing_receiving_utility_evidence",
        ),
        _component(
            "efficiency_context",
            _average_present(
                _stats_first_score(stats_first, "yards_after_catch_contact"),
                _stats_first_score(stats_first, "broken_tackle_context"),
                _stats_first_score(stats_first, "explosive_play_profile"),
            ),
            weights["efficiency_context"],
            "yards_after_catch_contact|broken_tackle_context|explosive_play_profile",
            "stats_first_historical_evidence",
            warning="missing_efficiency_context_evidence",
        ),
    )


def _wr_components(
    row: dict[str, str],
    vorp_row: dict[str, str] | None,
    max_vorp: float,
    max_first_down: float,
) -> tuple[_Component, ...]:
    stats = _json(row.get("factual_evidence_json")).get("rotowire_player_stats", {})
    derived = _json(row.get("derived_evidence_json"))
    stats_first = derived.get("stats_first_component_evidence", {})
    role_usage = derived.get("rotowire_role_usage", {})
    weights = COMPONENT_WEIGHTS["WR"]
    return (
        _vorp_component(vorp_row, max_vorp, weights["vorp_anchor"]),
        _component(
            "target_route_role",
            _average_present(
                _stats_first_score(stats_first, "target_carry_volume"),
                _stats_first_score(stats_first, "target_share_team_share"),
                _normalize(_stat(stats, "receiving:advanced", "routes_run_tprr"), 30.0),
                _normalize(_stat(stats, "receiving:advanced", "routes_run_yprr"), 3.0),
                _normalize(_metric(role_usage, "snaps", "snap_count_off_2"), 95.0),
            ),
            weights["target_route_role"],
            "target_carry_volume|target_share_team_share|routes_run_tprr|routes_run_yprr|snap_count_off_2",
            "stats_first_historical_evidence|imported_real_data|imported_snap_data",
            warning="missing_target_route_role_evidence",
        ),
        _component(
            "first_down_yardage",
            _average_present(
                _first_down_score(vorp_row, max_first_down),
                _stats_first_score(stats_first, "production_trend"),
                _normalize(_stat(stats, "receiving:basic", "receiving_yds_g"), 100.0),
            ),
            weights["first_down_yardage"],
            "imported_first_down_points|production_trend|receiving_yds_g",
            "imported_real_data|stats_first_historical_evidence",
            lane="replacement_vorp_review",
            warning="missing_first_down_yardage_evidence",
        ),
        _component(
            "air_yard_role",
            _average_present(
                _stats_first_score(stats_first, "air_yard_role"),
                _normalize(_stat(stats, "receiving:advanced", "team_ay"), 40.0),
                _normalize(
                    _stat(
                        stats,
                        "receiving:advanced",
                        "air_yards_ay_depth_of_target_adot",
                    ),
                    16.0,
                ),
            ),
            weights["air_yard_role"],
            "air_yard_role|team_ay|air_yards_ay_depth_of_target_adot",
            "stats_first_historical_evidence|imported_real_data",
            warning="missing_air_yard_role_evidence",
        ),
        _component(
            "efficiency_context",
            _average_present(
                _stats_first_score(stats_first, "yards_after_catch_contact"),
                _stats_first_score(stats_first, "explosive_play_profile"),
                _stats_first_score(stats_first, "drop_catchable_context"),
                _stats_first_score(stats_first, "broken_tackle_context"),
            ),
            weights["efficiency_context"],
            "yards_after_catch_contact|explosive_play_profile|drop_catchable_context|broken_tackle_context",
            "stats_first_historical_evidence",
            warning="missing_efficiency_context_evidence",
        ),
    )


def _vorp_component(
    vorp_row: dict[str, str] | None,
    max_vorp: float,
    weight: float,
) -> _Component:
    positive_vorp = _float((vorp_row or {}).get("positive_vorp_points"), None)
    score = _normalize(positive_vorp, max_vorp) if max_vorp > 0 else None
    return _Component(
        name="vorp_anchor",
        raw_value=positive_vorp,
        normalized_score=score,
        weight=weight,
        source_status="review_only_replacement_vorp_core",
        allowed_input_file=REPLACEMENT_VORP_PLAYER_ROWS,
        allowed_lane="replacement_vorp_review",
        allowed_field_or_json_path="positive_vorp_points|review_scoring_points",
        receipt_pointer="local_exports/model_v4/replacement_vorp/latest/player_vorp_receipts.csv",
        warning="" if score is not None else "missing_vorp_anchor",
    )


def _component(
    name: str,
    score: float | None,
    weight: float,
    field_path: str,
    source_status: str,
    *,
    lane: str = "derived_evidence_json",
    warning: str,
) -> _Component:
    return _Component(
        name=name,
        raw_value=score,
        normalized_score=score,
        weight=weight,
        source_status=source_status if score is not None else "missing_evidence",
        allowed_input_file=(
            REPLACEMENT_VORP_PLAYER_ROWS
            if lane == "replacement_vorp_review"
            else NFL_MATRIX
        ),
        allowed_lane=lane,
        allowed_field_or_json_path=field_path,
        receipt_pointer="local_exports/model_v4/.../phase_11c_component_receipts.csv",
        warning="" if score is not None else warning,
    )


def _confidence(
    components: tuple[_Component, ...],
    row: dict[str, str],
    vorp_row: dict[str, str] | None,
) -> tuple[float, str, tuple[str, ...]]:
    warnings: list[str] = []
    missing_components = [
        component for component in components if component.normalized_score is None
    ]
    multiplier = 1.0 - min(0.18, 0.045 * len(missing_components))
    first_down_status = str((vorp_row or {}).get("first_down_source_status") or "")
    if "missing_imported_first_downs" in first_down_status:
        multiplier -= 0.04
        warnings.append("first_down_missing_confidence_cap")
    elif "partial" in first_down_status:
        multiplier -= 0.02
        warnings.append("partial_first_down_confidence_cap")
    source_status = _json(row.get("source_status_json"))
    if "stats_first_historical_evidence" not in str(source_status.get("derived_evidence", "")):
        multiplier -= 0.05
        warnings.append("missing_stats_first_confidence_cap")
    multiplier = round(max(0.72, multiplier), 4)
    if multiplier >= 0.94:
        status = "high_review_confidence"
    elif multiplier >= 0.84:
        status = "medium_review_confidence"
    else:
        status = "low_review_confidence"
    return multiplier, status, tuple(warnings)


def _component_row(
    key: str,
    player_name: str,
    position: str,
    component: _Component,
) -> dict[str, object]:
    return {
        "canonical_player_key": key,
        "player_name": player_name,
        "position": position,
        "component_name": component.name,
        "raw_component_value": _blank_if_none(component.raw_value),
        "normalized_score": _blank_if_none(component.normalized_score),
        "component_weight": component.weight,
        "weighted_contribution": _blank_if_none(component.weighted_contribution),
        "source_status": component.source_status,
        "allowed_input_file": component.allowed_input_file,
        "allowed_lane": component.allowed_lane,
        "allowed_field_or_json_path": component.allowed_field_or_json_path,
        "receipt_pointer": component.receipt_pointer,
        "component_warning": component.warning,
        "formula_version": RB_WR_CURRENT_VALUE_VERSION,
    }


def _receipt_rows(
    key: str,
    player_name: str,
    position: str,
    row: dict[str, str],
    vorp_row: dict[str, str] | None,
) -> tuple[dict[str, object], ...]:
    receipt_pointers = _json(row.get("receipt_pointers_json"))
    rows = [
        _receipt(
            key,
            player_name,
            position,
            "rotowire_player_stats",
            receipt_pointers.get("rotowire_player_stats", ""),
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "factual_evidence_json",
            "rotowire_player_stats",
        ),
        _receipt(
            key,
            player_name,
            position,
            "rotowire_role_usage",
            receipt_pointers.get("rotowire_role_usage", ""),
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "derived_evidence_json",
            "rotowire_role_usage",
        ),
        _receipt(
            key,
            player_name,
            position,
            "stats_first_component_evidence",
            receipt_pointers.get("stats_first_components", ""),
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "derived_evidence_json",
            "stats_first_component_evidence",
        ),
    ]
    if vorp_row is not None:
        rows.append(
            _receipt(
                key,
                player_name,
                position,
                "replacement_vorp_review",
                "local_exports/model_v4/replacement_vorp/latest/player_vorp_receipts.csv",
                "review_only_replacement_vorp_core",
                REPLACEMENT_VORP_PLAYER_ROWS,
                "replacement_vorp_review",
                "positive_vorp_points|review_scoring_points|imported_first_down_points",
            )
        )
    return tuple(rows)


def _receipt(
    key: str,
    player_name: str,
    position: str,
    feature_group: str,
    pointer: object,
    source_status: str,
    input_file: str,
    lane: str,
    field_path: str,
) -> dict[str, object]:
    return {
        "canonical_player_key": key,
        "player_name": player_name,
        "position": position,
        "feature_group": feature_group,
        "receipt_pointer": pointer,
        "source_status": source_status,
        "allowed_input_file": input_file,
        "allowed_lane": lane,
        "allowed_field_or_json_path": field_path,
        "receipt_requirement": "Receipt pointer required for every consumed feature group.",
        "formula_version": RB_WR_CURRENT_VALUE_VERSION,
    }


def _warning_rows(
    key: str,
    player_name: str,
    position: str,
    warning_flags: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "entity_key": key,
            "player_name": player_name,
            "position": position,
            "warning_type": "current_value_review",
            "severity": "review",
            "warning_code": warning,
            "warning_detail": warning.replace("_", " "),
            "next_action": "Review before formula promotion; do not use as active app value.",
            "formula_version": RB_WR_CURRENT_VALUE_VERSION,
        }
        for warning in dict.fromkeys(warning_flags)
    )


def _warning_flag_list(value: object) -> list[str]:
    return [
        flag.strip()
        for flag in str(value or "").replace(";", "|").split("|")
        if flag.strip()
    ]


def _sanity_warnings(value_rows: list[dict[str, object]]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    if value_rows:
        rows.append(
            _sanity_warning(
                "rb_wr_balance_sanity",
                "RB/WR current value generated as review-only; inspect top "
                "cross-position ordering before promotion.",
            )
        )
    if any(
        row["position"] == "RB"
        and _float(row["receiving_utility_score"], 0.0) == 0
        for row in value_rows
    ):
        rows.append(
            _sanity_warning(
                "rb_receiving_role_missing_sanity",
                "At least one RB lacks receiving utility evidence; confidence caps "
                "should remain visible.",
            )
        )
    if any(row["position"] == "WR" and row["air_yard_role_score"] == "" for row in value_rows):
        rows.append(
            _sanity_warning(
                "wr_air_yard_missing_sanity",
                "At least one WR lacks air-yard role evidence; do not infer deep "
                "role from missing data.",
            )
        )
    return tuple(rows)


def _sanity_warning(code: str, detail: str) -> dict[str, object]:
    return {
        "entity_key": "phase_11c_sanity",
        "player_name": "",
        "position": "RB|WR",
        "warning_type": "sanity_fixture",
        "severity": "review",
        "warning_code": code,
        "warning_detail": detail,
        "next_action": "Use as audit fixture before app promotion planning.",
        "formula_version": RB_WR_CURRENT_VALUE_VERSION,
    }


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _vorp_index(path: Path) -> dict[str, dict[str, str]]:
    return {row["canonical_player_key"]: row for row in _read_rows(path)}


def _position_max_vorp(vorp_rows: dict[str, dict[str, str]]) -> dict[str, float]:
    max_by_position: dict[str, float] = {}
    for row in vorp_rows.values():
        position = row.get("position", "")
        if position not in SUPPORTED_POSITIONS:
            continue
        value = _float(row.get("positive_vorp_points"), 0.0)
        max_by_position[position] = max(max_by_position.get(position, 0.0), value)
    return max_by_position


def _position_max_first_down(vorp_rows: dict[str, dict[str, str]]) -> dict[str, float]:
    max_by_position: dict[str, float] = {}
    for row in vorp_rows.values():
        position = row.get("position", "")
        if position not in SUPPORTED_POSITIONS:
            continue
        value = _float(row.get("imported_first_down_points"), 0.0)
        max_by_position[position] = max(max_by_position.get(position, 0.0), value)
    return max_by_position


def _stats_first_score(stats_first: dict[str, Any], name: str) -> float | None:
    value = ((stats_first.get(name) or {}).get("normalized_score"))
    return _float(value, None)


def _stat(stats: dict[str, Any], group: str, metric: str) -> float | None:
    return _float(((stats.get(group) or {}).get("metrics") or {}).get(metric), None)


def _metric(role_usage: dict[str, Any], group: str, metric: str) -> float | None:
    return _float(((role_usage.get(group) or {}).get("metrics") or {}).get(metric), None)


def _first_down_score(vorp_row: dict[str, str] | None, max_first_down: float) -> float | None:
    if vorp_row is None or max_first_down <= 0:
        return None
    status = str(vorp_row.get("first_down_source_status") or "")
    if "imported_real_data" not in status:
        return None
    return _normalize(_float(vorp_row.get("imported_first_down_points"), None), max_first_down)


def _average_present(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def _normalize(value: float | None, ceiling: float) -> float | None:
    if value is None or ceiling <= 0:
        return None
    return round(max(0.0, min(100.0, (value / ceiling) * 100.0)), 4)


def _score_cell(components: dict[str, _Component], name: str) -> object:
    component = components.get(name)
    if component is None or component.normalized_score is None:
        return ""
    return component.normalized_score


def _json(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _float(value: object, default: float | None = 0.0) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _blank_if_none(value: object) -> object:
    return "" if value is None else value


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(
    path: Path,
    result: RbWrCurrentValueResult,
    outputs: RbWrCurrentValuePaths,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    top_rows = result.value_rows[:10]
    lines = [
        "# Phase 11C RB/WR Current Value",
        "",
        "## Purpose",
        "",
        "Phase 11C builds a review-only RB/WR current value layer. It uses Phase "
        "11A allowed fields and the Phase 11B review-only VORP core. It does not "
        "promote app surfaces, change active rankings, alter My Team or War Board, "
        "or unlock readiness gates.",
        "",
        "## Outputs",
        "",
        f"- `{outputs.value_rows}`",
        f"- `{outputs.component_rows}`",
        f"- `{outputs.receipts}`",
        f"- `{outputs.warnings}`",
        "",
        "## Formula Shape",
        "",
        "RB current value uses VORP anchor, role/volume, first-down/high-value "
        "usage, receiving utility, and efficiency context.",
        "",
        "WR current value uses VORP anchor, target/route role, first-down/yardage "
        "production, air-yard role, and efficiency context.",
        "",
        "Missing components are not converted to zero or average. Available "
        "components are rescaled, then confidence caps reduce the review score "
        "when evidence is missing or partial.",
        "",
        "## Safety Rules",
        "",
        "- Review-only outputs.",
        "- No market, projection, ADP, ranking, mock, big-board, or consensus inputs.",
        "- First-down value comes through Phase 11B admitted first-down handling.",
        "- Return scoring remains direct scoring context only and is not a talent or role signal.",
        "- No active app ranking, My Team, War Board, or readiness changes.",
        "",
        "## Summary",
        "",
        f"- Player rows: {result.summary['player_rows']}",
        f"- Component rows: {result.summary['component_rows']}",
        f"- Receipt rows: {result.summary['receipt_rows']}",
        f"- Warning rows: {result.summary['warning_rows']}",
        f"- Market rows used: {result.summary['market_rows_used']}",
        f"- Projection rows used: {result.summary['projection_rows_used']}",
        "",
        "## Top Review Rows",
        "",
        "| Player | Pos | Team | Review Score | Confidence |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in top_rows:
        lines.append(
            "| {player} | {position} | {team} | {score} | {confidence} |".format(
                player=row["player_name"],
                position=row["position"],
                team=row["nfl_team"],
                score=row["current_value_review_score"],
                confidence=row["confidence_status"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
