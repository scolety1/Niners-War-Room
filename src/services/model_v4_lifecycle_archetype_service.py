from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_formula_contract_service import (
    NFL_MATRIX,
    ROOKIE_AGE_SOURCE,
    SLEEPER_PLAYER_AGE_SOURCE,
    WARNING_MATRIX,
    assert_formula_field_allowed,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_11E_LIFECYCLE_ARCHETYPE_LAYER.md")

LIFECYCLE_ARCHETYPE_VERSION = "model_v4_phase_11e_lifecycle_archetype_0.1.0"
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")

REVIEW_HEADER = (
    "canonical_player_key",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "lifecycle_expected",
    "role_archetype",
    "lifecycle_modifier_review",
    "confidence_multiplier",
    "age_years_decimal",
    "age_total_months",
    "age_evidence_status",
    "role_fragility_status",
    "primary_role_receipt",
    "secondary_role_receipt",
    "allowed_use",
    "warning_flags",
    "lifecycle_version",
)

COMPONENT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "component_name",
    "component_value",
    "component_score",
    "source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_pointer",
    "component_warning",
    "lifecycle_version",
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
    "lifecycle_version",
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
    "lifecycle_version",
)


@dataclass(frozen=True)
class LifecycleArchetypeResult:
    review_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class LifecycleArchetypePaths:
    review_rows: Path
    component_rows: Path
    receipts: Path
    warnings: Path
    doc: Path


@dataclass(frozen=True)
class _Component:
    name: str
    value: str
    score: float | None
    source_status: str
    allowed_input_file: str
    allowed_lane: str
    allowed_field_or_json_path: str
    receipt_pointer: str
    warning: str = ""


def build_lifecycle_archetype_layer(
    *,
    nfl_matrix_path: str | Path = NFL_MATRIX,
    warning_matrix_path: str | Path = WARNING_MATRIX,
    age_source_paths: tuple[str | Path, ...] = (ROOKIE_AGE_SOURCE, SLEEPER_PLAYER_AGE_SOURCE),
) -> LifecycleArchetypeResult:
    _assert_phase_11e_contract()
    warning_index = _warning_index(Path(warning_matrix_path))
    age_index = _combined_age_index(age_source_paths)
    review_rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    age_rows_used = 0
    for row in _read_rows(Path(nfl_matrix_path)):
        position = str(row.get("position") or "")
        if position not in SUPPORTED_POSITIONS:
            continue
        key = str(row.get("canonical_player_key") or "")
        age_row = age_index.get(str(row.get("normalized_player_name") or ""))
        if age_row is not None:
            age_rows_used += 1
        player = _lifecycle_row(row, warning_index.get(key, ()), age_row)
        review_rows.append(player["review_row"])
        component_rows.extend(player["component_rows"])
        receipt_rows.extend(player["receipt_rows"])
        warning_rows.extend(player["warning_rows"])
    warning_rows.extend(_sanity_warnings())
    summary = {
        "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
        "review_status": "review_only",
        "player_rows": len(review_rows),
        "component_rows": len(component_rows),
        "receipt_rows": len(receipt_rows),
        "warning_rows": len(warning_rows),
        "market_rows_used": 0,
        "projection_rows_used": 0,
        "age_rows_used": age_rows_used,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return LifecycleArchetypeResult(
        review_rows=tuple(review_rows),
        component_rows=tuple(component_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary=summary,
    )


def write_lifecycle_archetype_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: LifecycleArchetypeResult | None = None,
) -> LifecycleArchetypePaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_lifecycle_archetype_layer()
    paths = LifecycleArchetypePaths(
        review_rows=output / "lifecycle_archetype_review_rows.csv",
        component_rows=output / "lifecycle_archetype_component_rows.csv",
        receipts=output / "lifecycle_archetype_receipts.csv",
        warnings=output / "lifecycle_archetype_warnings.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.review_rows, REVIEW_HEADER, result.review_rows)
    _write_csv(paths.component_rows, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_doc(paths.doc, result, paths)
    return paths


def _assert_phase_11e_contract() -> None:
    for lane, path in (
        ("row_metadata", "position|lifecycle_expected"),
        ("factual_evidence_json", "rotowire_player_stats"),
        ("derived_evidence_json", "rotowire_role_usage"),
    ):
        assert_formula_field_allowed(
            module_name="lifecycle_archetype",
            allowed_input_file=NFL_MATRIX,
            allowed_lane=lane,
            allowed_field_or_json_path=path,
        )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=ROOKIE_AGE_SOURCE,
        allowed_lane="player_age_intake_csv",
        allowed_field_or_json_path="age_years_decimal|age_total_months",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=SLEEPER_PLAYER_AGE_SOURCE,
        allowed_lane="sleeper_player_age_csv",
        allowed_field_or_json_path="age_years_decimal|age_total_months",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=WARNING_MATRIX,
        allowed_lane="warnings",
        allowed_field_or_json_path="warning_code|severity|warning_detail",
        private_value=False,
    )


def _lifecycle_row(
    row: dict[str, str],
    source_warnings: tuple[dict[str, str], ...],
    age_row: dict[str, str] | None,
) -> dict[str, object]:
    position = str(row.get("position") or "")
    factual = _json(row.get("factual_evidence_json"))
    derived = _json(row.get("derived_evidence_json"))
    stats = factual.get("rotowire_player_stats", {})
    role_usage = derived.get("rotowire_role_usage", {})
    archetype, modifier, fragility, role_receipts, warnings = _classify_position(
        position, stats, role_usage
    )
    age_years = _float((age_row or {}).get("age_years_decimal"), None)
    age_months = _float((age_row or {}).get("age_total_months"), None)
    age_status = _age_status(age_row, age_years)
    if position == "QB" and "rushing" in archetype:
        if age_years is None:
            warnings.append("qb_rushing_age_caution_unavailable")
        elif age_years >= 29.0:
            warnings.append("qb_rushing_age_caution_active")
    if position == "RB":
        if age_years is None:
            warnings.append("rb_age_cliff_guardrail_unavailable")
        elif age_years >= 29.0:
            warnings.append("rb_age_cliff_guardrail_active")
        elif age_years >= 27.0:
            warnings.append("rb_age_window_caution_active")
    confidence = round(max(0.78, 1.0 - (0.04 * len(warnings))), 4)
    key = str(row.get("canonical_player_key") or "")
    player_name = str(row.get("player_name") or "")
    source_warning_codes = tuple(
        warning["warning_code"]
        for warning in source_warnings
        if warning.get("warning_code") in {
            "missing_rotowire_player_stats",
            "missing_stats_first_component_evidence",
            "team_mismatch_or_missing_model_team",
        }
    )
    warning_flags = tuple(dict.fromkeys([*warnings, *source_warning_codes]))
    components = _components(
        row,
        archetype,
        modifier,
        confidence,
        fragility,
        age_status,
        age_row,
        age_years,
        age_months,
        role_receipts,
    )
    review_row = {
        "canonical_player_key": key,
        "player_name": player_name,
        "normalized_player_name": row.get("normalized_player_name", ""),
        "position": position,
        "nfl_team": row.get("nfl_team", ""),
        "lifecycle_expected": row.get("lifecycle_expected", ""),
        "role_archetype": archetype,
        "lifecycle_modifier_review": modifier,
        "confidence_multiplier": confidence,
        "age_years_decimal": "" if age_years is None else age_years,
        "age_total_months": "" if age_months is None else age_months,
        "age_evidence_status": age_status,
        "role_fragility_status": fragility,
        "primary_role_receipt": role_receipts[0],
        "secondary_role_receipt": role_receipts[1],
        "allowed_use": "review_only_lifecycle_archetype",
        "warning_flags": "|".join(warning_flags),
        "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
    }
    return {
        "review_row": review_row,
        "component_rows": tuple(_component_row(key, player_name, position, c) for c in components),
        "receipt_rows": _receipt_rows(key, player_name, position, age_row),
        "warning_rows": _warning_rows(key, player_name, position, warning_flags),
    }


def _classify_position(
    position: str,
    stats: dict[str, Any],
    role_usage: dict[str, Any],
) -> tuple[str, float, str, tuple[str, str], list[str]]:
    if position == "QB":
        return _classify_qb(stats)
    if position == "RB":
        return _classify_rb(stats, role_usage)
    if position == "WR":
        return _classify_wr(stats, role_usage)
    return _classify_te(stats, role_usage)


def _classify_qb(
    stats: dict[str, Any],
) -> tuple[str, float, str, tuple[str, str], list[str]]:
    rush_yards = _stat(stats, "passing:basic", "rushing_yds")
    rush_att = _stat(stats, "passing:basic", "rushing_att")
    pass_att = _stat(stats, "passing:basic", "passing_att")
    pass_yards = _stat(stats, "passing:basic", "passing_yds")
    warnings: list[str] = []
    if rush_yards is None or rush_att is None:
        warnings.append("missing_qb_rushing_lifecycle_evidence")
    if pass_att is None or pass_yards is None:
        warnings.append("missing_qb_passing_lifecycle_evidence")
    rush_score = _average_present(_normalize(rush_yards, 750.0), _normalize(rush_att, 125.0))
    pass_score = _average_present(_normalize(pass_att, 650.0), _normalize(pass_yards, 5200.0))
    if (rush_score or 0.0) >= 55 and (pass_score or 0.0) >= 45:
        return (
            "qb_hybrid_rushing_passing_engine",
            1.02,
            "rushing_age_review_needed",
            ("rushing_yds|rushing_att", "passing_att|passing_yds"),
            warnings,
        )
    if (rush_score or 0.0) >= 45:
        return (
            "qb_rushing_dependent",
            0.98,
            "rushing_age_review_needed",
            ("rushing_yds|rushing_att", "red_zone_rush_att_in10"),
            warnings,
        )
    return (
        "qb_pocket_leaning",
        0.96 if (pass_score or 0.0) < 45 else 1.0,
        "one_qb_vorp_dependency_review",
        ("passing_att|passing_yds", "passing_td|passing_qbr"),
        warnings,
    )


def _classify_rb(
    stats: dict[str, Any],
    role_usage: dict[str, Any],
) -> tuple[str, float, str, tuple[str, str], list[str]]:
    rush_att = _stat(stats, "rushing:basic", "rushing_att")
    targets = _stat(stats, "receiving:advanced", "receiving_tar")
    snap_pct = _metric(role_usage, "snaps", "snap_count_off_2")
    warnings: list[str] = []
    if rush_att is None:
        warnings.append("missing_rb_carry_lifecycle_evidence")
    if targets is None:
        warnings.append("missing_rb_receiving_lifecycle_evidence")
    if snap_pct is None:
        warnings.append("missing_rb_snap_lifecycle_evidence")
    carry_score = _normalize(rush_att, 300.0) or 0.0
    target_score = _normalize(targets, 90.0) or 0.0
    snap_score = _normalize(snap_pct, 85.0) or 0.0
    if carry_score >= 65 and target_score >= 45 and snap_score >= 65:
        return (
            "rb_short_window_three_down_role_asset",
            1.04,
            "rb_role_strong_but_age_sensitive",
            ("rushing_att|snap_count_off_2", "receiving_tar"),
            warnings,
        )
    if carry_score >= 65:
        return (
            "rb_short_window_rushing_role_asset",
            0.99,
            "rb_receiving_role_fragility_review",
            ("rushing_att|snap_count_off_2", "receiving_tar"),
            warnings,
        )
    return (
        "rb_role_fragility_review",
        0.92,
        "rb_role_not_stable_enough_for_lifecycle_boost",
        ("rushing_att", "snap_count_off_2|receiving_tar"),
        warnings,
    )


def _classify_wr(
    stats: dict[str, Any],
    role_usage: dict[str, Any],
) -> tuple[str, float, str, tuple[str, str], list[str]]:
    target_share = _stat(stats, "receiving:advanced", "team_tar")
    tprr = _stat(stats, "receiving:advanced", "routes_run_tprr")
    yprr = _stat(stats, "receiving:advanced", "routes_run_yprr")
    adot = _stat(stats, "receiving:advanced", "air_yards_ay_depth_of_target_adot")
    ypc = _stat(stats, "receiving:basic", "receiving_ypc")
    slot = _metric(role_usage, "alignment", "grouped_slot")
    out = _metric(role_usage, "alignment", "grouped_out")
    warnings: list[str] = []
    if target_share is None or tprr is None:
        warnings.append("missing_wr_target_lifecycle_evidence")
    if yprr is None:
        warnings.append("missing_wr_route_efficiency_lifecycle_evidence")
    target_score = _average_present(_normalize(target_share, 30.0), _normalize(tprr, 30.0)) or 0.0
    if target_score >= 60 and (yprr or 0.0) >= 1.8:
        return (
            "wr_target_earner",
            1.04,
            "wr_role_durable_if_route_volume_holds",
            ("team_tar|routes_run_tprr", "routes_run_yprr"),
            warnings,
        )
    if (adot or 0.0) >= 12 and (ypc or 0.0) >= 14 and target_score < 55:
        return (
            "wr_speed_dependent_field_stretcher",
            0.95,
            "wr_speed_efficiency_fragility_review",
            ("air_yards_ay_depth_of_target_adot|receiving_ypc", "team_tar"),
            warnings,
        )
    if (slot or 0.0) >= (out or 0.0) * 0.5 and target_score >= 40:
        return (
            "wr_possession_chain_mover",
            1.01,
            "wr_format_fit_depends_on_first_downs_not_receptions",
            ("grouped_slot|team_tar", "routes_run_tprr"),
            warnings,
        )
    return (
        "wr_role_fragility_review",
        0.93,
        "wr_role_not_stable_enough_for_lifecycle_boost",
        ("team_tar|routes_run_tprr", "routes_run_yprr"),
        warnings,
    )


def _classify_te(
    stats: dict[str, Any],
    role_usage: dict[str, Any],
) -> tuple[str, float, str, tuple[str, str], list[str]]:
    route_pct = _metric(role_usage, "te_routes", "route_data_route")
    route_targets = _metric(role_usage, "te_routes", "route_data_targets")
    blocking_pct = _metric(role_usage, "te_routes", "route_data_blocking")
    yprr = _stat(stats, "receiving:advanced", "routes_run_yprr")
    red_zone = _stat(stats, "receiving:redzone", "red_zone_targets_in20")
    warnings: list[str] = []
    if route_pct is None or route_targets is None:
        warnings.append("missing_te_route_lifecycle_evidence")
    if yprr is None:
        warnings.append("missing_te_yprr_lifecycle_evidence")
    if (route_pct or 0.0) >= 55 and (route_targets or 0.0) >= 60 and (yprr or 0.0) >= 1.5:
        return (
            "te_route_target_engine",
            1.04,
            "te_no_premium_value_supported_by_routes",
            ("route_data_route|route_data_targets", "routes_run_yprr"),
            warnings,
        )
    if (blocking_pct or 0.0) >= 12 or (route_pct is not None and route_pct < 45):
        return (
            "te_blocking_snap_risk",
            0.90,
            "te_snap_share_without_routes_risk",
            ("route_data_blocking|route_data_route", "routes_run_yprr"),
            warnings,
        )
    if (red_zone or 0.0) >= 10 and (route_targets or 0.0) < 60:
        return (
            "te_td_dependent",
            0.92,
            "te_td_role_without_full_route_engine",
            ("red_zone_targets_in20", "route_data_targets"),
            warnings,
        )
    return (
        "te_receiving_role_fragility_review",
        0.94,
        "te_no_premium_gap_requires_more_route_evidence",
        ("route_data_route|route_data_targets", "routes_run_yprr"),
        warnings,
    )


def _components(
    row: dict[str, str],
    archetype: str,
    modifier: float,
    confidence: float,
    fragility: str,
    age_status: str,
    age_row: dict[str, str] | None,
    age_years: float | None,
    age_months: float | None,
    role_receipts: tuple[str, str],
) -> tuple[_Component, ...]:
    age_source_status = (
        str(
            age_row.get("source_status")
            or "user_provided_age_source_formula_admitted_after_validation"
        )
        if age_row is not None
        else "missing_age_evidence"
    )
    age_input_file = str((age_row or {}).get("allowed_input_file") or ROOKIE_AGE_SOURCE)
    age_lane = str((age_row or {}).get("allowed_lane") or "player_age_intake_csv")
    if age_row is None:
        age_input_file = NFL_MATRIX
        age_lane = "row_metadata"
    age_path = (
        "age_years_decimal|age_total_months"
        if age_row is not None
        else "position|lifecycle_expected"
    )
    age_receipt = (
        f"{age_input_file}:{age_row.get('normalized_player_name', '')}"
        if age_row is not None
        else "local_exports/model_v4/.../lifecycle_archetype_receipts.csv"
    )
    age_component_warning = "" if age_row is not None else "age_not_fabricated"
    age_value = (
        f"{age_years}|{age_months}"
        if age_years is not None and age_months is not None
        else age_status
    )
    return (
        _Component(
            "lifecycle_bucket",
            str(row.get("lifecycle_expected") or ""),
            None,
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "row_metadata",
            "position|lifecycle_expected",
            "local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv",
        ),
        _Component(
            "role_archetype",
            archetype,
            modifier,
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "factual_evidence_json",
            "rotowire_player_stats",
            "local_exports/model_v4/.../lifecycle_archetype_receipts.csv",
        ),
        _Component(
            "age_guardrail",
            age_value,
            confidence,
            age_source_status,
            age_input_file,
            age_lane,
            age_path,
            age_receipt,
            age_component_warning,
        ),
        _Component(
            "role_fragility",
            fragility,
            confidence,
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "derived_evidence_json",
            "rotowire_role_usage",
            "local_exports/model_v4/.../lifecycle_archetype_receipts.csv",
        ),
        _Component(
            "role_receipt_detail",
            "|".join(role_receipts),
            None,
            "formula_admitted_after_validation",
            NFL_MATRIX,
            "factual_evidence_json",
            "rotowire_player_stats",
            "local_exports/model_v4/.../lifecycle_archetype_receipts.csv",
        ),
    )


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
        "component_value": component.value,
        "component_score": "" if component.score is None else component.score,
        "source_status": component.source_status,
        "allowed_input_file": component.allowed_input_file,
        "allowed_lane": component.allowed_lane,
        "allowed_field_or_json_path": component.allowed_field_or_json_path,
        "receipt_pointer": component.receipt_pointer,
        "component_warning": component.warning,
        "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
    }


def _receipt_rows(
    key: str,
    player_name: str,
    position: str,
    age_row: dict[str, str] | None,
) -> tuple[dict[str, object], ...]:
    rows = [
        _receipt(
            key,
            player_name,
            position,
            "row_metadata",
            NFL_MATRIX,
            "row_metadata",
            "position|lifecycle_expected",
        ),
        _receipt(
            key,
            player_name,
            position,
            "rotowire_player_stats",
            NFL_MATRIX,
            "factual_evidence_json",
            "rotowire_player_stats",
        ),
        _receipt(
            key,
            player_name,
            position,
            "rotowire_role_usage",
            NFL_MATRIX,
            "derived_evidence_json",
            "rotowire_role_usage",
        ),
    ]
    if age_row is not None:
        rows.append(
            {
                "canonical_player_key": key,
                "player_name": player_name,
                "position": position,
                "feature_group": "player_age_intake",
                "receipt_pointer": (
                    f"{age_row.get('allowed_input_file') or ROOKIE_AGE_SOURCE}:"
                    f"{age_row.get('normalized_player_name', '')}"
                ),
                "source_status": (
                    age_row.get("source_status")
                    or "user_provided_age_source_formula_admitted_after_validation"
                ),
                "allowed_input_file": age_row.get("allowed_input_file") or ROOKIE_AGE_SOURCE,
                "allowed_lane": age_row.get("allowed_lane") or "player_age_intake_csv",
                "allowed_field_or_json_path": "age_years_decimal|age_total_months",
                "receipt_requirement": (
                    "Age sidecar receipt required for lifecycle age guardrails."
                ),
                "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
            }
        )
    return tuple(rows)


def _receipt(
    key: str,
    player_name: str,
    position: str,
    feature_group: str,
    input_file: str,
    lane: str,
    field_path: str,
) -> dict[str, object]:
    return {
        "canonical_player_key": key,
        "player_name": player_name,
        "position": position,
        "feature_group": feature_group,
        "receipt_pointer": input_file,
        "source_status": "formula_admitted_after_validation",
        "allowed_input_file": input_file,
        "allowed_lane": lane,
        "allowed_field_or_json_path": field_path,
        "receipt_requirement": "Receipt pointer required for every consumed feature group.",
        "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
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
            "warning_type": "lifecycle_review",
            "severity": "review",
            "warning_code": warning,
            "warning_detail": warning.replace("_", " "),
            "next_action": (
                "Use as confidence context; do not fabricate missing lifecycle evidence."
            ),
            "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
        }
        for warning in dict.fromkeys(warning_flags)
    )


def _warning_index(path: Path) -> dict[str, tuple[dict[str, str], ...]]:
    if not path.exists():
        return {}
    output: dict[str, list[dict[str, str]]] = {}
    for row in _read_rows(path):
        output.setdefault(str(row.get("entity_key") or ""), []).append(row)
    return {key: tuple(rows) for key, rows in output.items()}


def _combined_age_index(paths: tuple[str | Path, ...]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for path in paths:
        for key, row in _age_index(Path(path)).items():
            output.setdefault(key, row)
    return output


def _age_index(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    output: dict[str, dict[str, str]] = {}
    for row in _read_rows(path):
        if _float(row.get("age_years_decimal"), None) is None:
            continue
        row = {
            **row,
            "allowed_input_file": str(path).replace("\\", "/"),
            "allowed_lane": _age_lane(path),
        }
        for key in _age_lookup_keys(row):
            output.setdefault(key, row)
    return output


def _age_lane(path: Path) -> str:
    if str(path).replace("\\", "/") == SLEEPER_PLAYER_AGE_SOURCE:
        return "sleeper_player_age_csv"
    return "player_age_intake_csv"


def _age_lookup_keys(row: dict[str, str]) -> tuple[str, ...]:
    keys = [str(row.get("normalized_player_name") or "")]
    player = str(row.get("player") or "")
    without_suffix = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", player, flags=re.IGNORECASE)
    keys.append(_normalize_name(without_suffix))
    keys.append(re.sub(r"i{1,3}$", "", keys[0]))
    return tuple(key for key in dict.fromkeys(keys) if key)


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _age_status(age_row: dict[str, str] | None, age_years: float | None) -> str:
    if age_row is None or age_years is None:
        return "age_not_available_in_lifecycle_age_sidecar"
    return "matched_player_age_evidence"


def _sanity_warnings() -> tuple[dict[str, object], ...]:
    codes = {
        "lifecycle_age_sidecar_sanity": (
            "Age guardrails use the admitted player-age sidecar when a player match exists."
        ),
        "rb_short_window_sanity": "RB archetypes are short-window and role-sensitive.",
        "wr_role_shape_sanity": (
            "WR archetypes separate target earners from speed-dependent profiles."
        ),
        "qb_rushing_age_caution_sanity": (
            "QB rushing-age caution is explicit when age evidence is old or unavailable."
        ),
        "te_route_requirement_sanity": (
            "TE archetypes require route/target evidence in no-premium format."
        ),
    }
    return tuple(
        {
            "entity_key": "phase_11e_sanity",
            "player_name": "",
            "position": "QB|RB|WR|TE",
            "warning_type": "sanity_fixture",
            "severity": "review",
            "warning_code": code,
            "warning_detail": detail,
            "next_action": "Use as audit fixture before app promotion planning.",
            "lifecycle_version": LIFECYCLE_ARCHETYPE_VERSION,
        }
        for code, detail in codes.items()
    )


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _stat(stats: dict[str, Any], group: str, metric: str) -> float | None:
    return _float(((stats.get(group) or {}).get("metrics") or {}).get(metric), None)


def _metric(role_usage: dict[str, Any], group: str, metric: str) -> float | None:
    return _float(((role_usage.get(group) or {}).get("metrics") or {}).get(metric), None)


def _average_present(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def _normalize(value: float | None, ceiling: float) -> float | None:
    if value is None or ceiling <= 0:
        return None
    return round(max(0.0, min(100.0, (value / ceiling) * 100.0)), 4)


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
    result: LifecycleArchetypeResult,
    outputs: LifecycleArchetypePaths,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = result.review_rows[:12]
    lines = [
        "# Phase 11E Lifecycle And Archetype Layer",
        "",
        "## Purpose",
        "",
        "Phase 11E creates review-only lifecycle and role-archetype labels. These "
        "labels explain role shape, age guardrails, and fragility; they do not "
        "overwrite current-value evidence or active app rankings.",
        "",
        "## Outputs",
        "",
        f"- `{outputs.review_rows}`",
        f"- `{outputs.component_rows}`",
        f"- `{outputs.receipts}`",
        f"- `{outputs.warnings}`",
        "",
        "## Source Rules",
        "",
        "- Uses only Phase 11A lifecycle fields plus the admitted player-age sidecar.",
        "- Missing age remains missing; matched ages carry sidecar receipts.",
        "- No injury, athletic, route, market, projection, ADP, ranking, mock, "
        "or big-board fields are fabricated or consumed.",
        "",
        "## Summary",
        "",
        f"- Player rows: {result.summary['player_rows']}",
        f"- Component rows: {result.summary['component_rows']}",
        f"- Receipt rows: {result.summary['receipt_rows']}",
        f"- Warning rows: {result.summary['warning_rows']}",
        f"- Age rows used: {result.summary['age_rows_used']}",
        f"- Market rows used: {result.summary['market_rows_used']}",
        "",
        "## Sample Review Rows",
        "",
        "| Player | Pos | Archetype | Modifier | Confidence |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {player} | {position} | {archetype} | {modifier} | {confidence} |".format(
                player=row["player_name"],
                position=row["position"],
                archetype=row["role_archetype"],
                modifier=row["lifecycle_modifier_review"],
                confidence=row["confidence_multiplier"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
