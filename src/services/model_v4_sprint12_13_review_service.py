from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_formula_contract_service import (
    ADMITTED_PROSPECT_MATRIX,
    DRAFT_CAPITAL_SOURCE,
    ROOKIE_AGE_SOURCE,
    assert_formula_field_allowed,
)
from src.services.model_v4_rookie_age_intake_service import DEFAULT_ROOKIE_AGE_OUTPUT

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4")
CURRENT_VALUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
CURRENT_VALUE_COMPONENTS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_component_rows.csv"
)
CURRENT_VALUE_RECEIPTS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_receipts.csv"
)
CURRENT_VALUE_WARNINGS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_warnings.csv"
)
CONFIDENCE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/confidence_missingness_review_rows.csv"
)
ROOKIE_AGE_ROWS = DEFAULT_ROOKIE_AGE_OUTPUT
DRAFT_CAPITAL_ROWS = Path(
    "local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv"
)

SPRINT_12_13_VERSION = "model_v4_sprint_12_13_review_0.1.1"

PROSPECT_REVIEW_HEADER = (
    "canonical_prospect_key",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_year",
    "prospect_private_value_review_score",
    "confidence_cap",
    "confidence_status",
    "production_score",
    "market_share_score",
    "draft_capital_score",
    "athletic_prior_score",
    "recruiting_prior_score",
    "age_lifecycle_score",
    "age_years_decimal",
    "rookie_formula_balance_label",
    "landing_context_review",
    "component_weight_available",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

COMPONENT_HEADER = (
    "entity_key",
    "entity_name",
    "entity_type",
    "component_layer",
    "component_name",
    "component_value",
    "normalized_score",
    "component_weight",
    "weighted_contribution",
    "source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "component_warning",
    "formula_version",
)

RECEIPT_HEADER = (
    "entity_key",
    "entity_name",
    "entity_type",
    "receipt_layer",
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
    "entity_name",
    "entity_type",
    "position",
    "warning_layer",
    "warning_type",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)

PICK_BASELINE_HEADER = (
    "pick_asset_key",
    "season",
    "round",
    "pick_slot",
    "pick_label",
    "pick_value_review_score",
    "tier_label",
    "confidence_status",
    "allowed_use",
    "warning_flags",
    "formula_version",
)

DYNASTY_REVIEW_HEADER = (
    "asset_key",
    "asset_name",
    "asset_type",
    "position",
    "team_or_college",
    "dynasty_asset_value_review_score",
    "source_value_score",
    "confidence_cap",
    "value_source_layer",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)


@dataclass(frozen=True)
class Sprint1213ReviewResult:
    prospect_rows: tuple[dict[str, object], ...]
    prospect_component_rows: tuple[dict[str, object], ...]
    prospect_receipt_rows: tuple[dict[str, object], ...]
    prospect_warning_rows: tuple[dict[str, object], ...]
    pick_rows: tuple[dict[str, object], ...]
    dynasty_rows: tuple[dict[str, object], ...]
    dynasty_component_rows: tuple[dict[str, object], ...]
    dynasty_receipt_rows: tuple[dict[str, object], ...]
    dynasty_warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class Sprint1213ReviewPaths:
    prospect_review_rows: Path
    prospect_component_rows: Path
    prospect_receipts: Path
    prospect_warnings: Path
    pick_baselines: Path
    dynasty_review_rows: Path
    dynasty_component_rows: Path
    dynasty_receipts: Path
    dynasty_warnings: Path
    sprint12_doc: Path
    sprint13_doc: Path


def build_sprint12_13_review_outputs(
    *,
    admitted_prospect_matrix_path: str | Path = ADMITTED_PROSPECT_MATRIX,
    confidence_rows_path: str | Path = CONFIDENCE_ROWS,
    rookie_age_rows_path: str | Path = ROOKIE_AGE_ROWS,
    draft_capital_rows_path: str | Path = DRAFT_CAPITAL_ROWS,
    current_value_rows_path: str | Path = CURRENT_VALUE_ROWS,
    current_component_rows_path: str | Path = CURRENT_VALUE_COMPONENTS,
    current_receipt_rows_path: str | Path = CURRENT_VALUE_RECEIPTS,
    current_warning_rows_path: str | Path = CURRENT_VALUE_WARNINGS,
) -> Sprint1213ReviewResult:
    _assert_prospect_contract()
    confidence_by_key = _index(_read_rows(Path(confidence_rows_path)), "entity_key")
    age_by_name = _index(_read_rows(Path(rookie_age_rows_path)), "normalized_player_name")
    draft_capital_by_name = _index(
        _read_rows(Path(draft_capital_rows_path)),
        "normalized_player_name",
    )
    prospect_rows_raw = _read_rows(Path(admitted_prospect_matrix_path))
    prospect_rows: list[dict[str, object]] = []
    prospect_components: list[dict[str, object]] = []
    prospect_receipts: list[dict[str, object]] = []
    prospect_warnings: list[dict[str, object]] = []
    for row in prospect_rows_raw:
        built = _prospect_value_row(
            row,
            confidence_by_key.get(row["canonical_prospect_key"], {}),
            age_by_name.get(_normalize_name(row.get("prospect_name", "")), {}),
            draft_capital_by_name.get(row.get("normalized_player_name", ""))
            or draft_capital_by_name.get(_normalize_name(row.get("prospect_name", "")), {}),
        )
        prospect_rows.append(built["review_row"])
        prospect_components.extend(built["component_rows"])
        prospect_receipts.extend(built["receipt_rows"])
        prospect_warnings.extend(built["warning_rows"])
    pick_rows = _pick_baselines()
    current_rows = _read_rows(Path(current_value_rows_path))
    dynasty_rows = (
        *_current_asset_rows(current_rows),
        *_prospect_asset_rows(tuple(prospect_rows)),
        *_pick_asset_rows(pick_rows),
    )
    dynasty_components = (
        *_current_asset_components(_read_rows(Path(current_component_rows_path))),
        *_prospect_asset_components(tuple(prospect_components)),
        *_pick_asset_components(pick_rows),
    )
    dynasty_receipts = (
        *_current_asset_receipts(_read_rows(Path(current_receipt_rows_path))),
        *_prospect_asset_receipts(tuple(prospect_receipts)),
        *_pick_asset_receipts(pick_rows),
    )
    dynasty_warnings = (
        *_current_asset_warnings(_read_rows(Path(current_warning_rows_path))),
        *_prospect_asset_warnings(tuple(prospect_warnings)),
        *_pick_asset_warnings(pick_rows),
        *_dynasty_sanity_warnings(tuple(dynasty_rows)),
    )
    summary = {
        "formula_version": SPRINT_12_13_VERSION,
        "review_status": "review_only",
        "prospect_rows": len(prospect_rows),
        "pick_rows": len(pick_rows),
        "dynasty_asset_rows": len(dynasty_rows),
        "market_rows_used_for_private_value": 0,
        "projection_rows_used_for_private_value": 0,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return Sprint1213ReviewResult(
        prospect_rows=tuple(prospect_rows),
        prospect_component_rows=tuple(prospect_components),
        prospect_receipt_rows=tuple(prospect_receipts),
        prospect_warning_rows=tuple(prospect_warnings),
        pick_rows=pick_rows,
        dynasty_rows=tuple(dynasty_rows),
        dynasty_component_rows=tuple(dynasty_components),
        dynasty_receipt_rows=tuple(dynasty_receipts),
        dynasty_warning_rows=tuple(dynasty_warnings),
        summary=summary,
    )


def write_sprint12_13_review_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: Sprint1213ReviewResult | None = None,
) -> Sprint1213ReviewPaths:
    output = Path(output_root)
    result = result or build_sprint12_13_review_outputs()
    prospect_dir = output / "prospect_value/latest"
    pick_dir = output / "pick_values/latest"
    dynasty_dir = output / "dynasty_asset_value/latest"
    docs_dir = Path("docs/model_v4")
    for folder in (prospect_dir, pick_dir, dynasty_dir, docs_dir):
        folder.mkdir(parents=True, exist_ok=True)
    paths = Sprint1213ReviewPaths(
        prospect_review_rows=prospect_dir / "prospect_value_review_rows.csv",
        prospect_component_rows=prospect_dir / "prospect_value_component_rows.csv",
        prospect_receipts=prospect_dir / "prospect_value_receipts.csv",
        prospect_warnings=prospect_dir / "prospect_value_warnings.csv",
        pick_baselines=pick_dir / "pick_value_baselines_review.csv",
        dynasty_review_rows=dynasty_dir / "dynasty_asset_value_review_rows.csv",
        dynasty_component_rows=dynasty_dir / "dynasty_asset_value_component_rows.csv",
        dynasty_receipts=dynasty_dir / "dynasty_asset_value_receipts.csv",
        dynasty_warnings=dynasty_dir / "dynasty_asset_value_warnings.csv",
        sprint12_doc=docs_dir / "SPRINT_12_REVIEW_ONLY_DYNASTY_VALUE.md",
        sprint13_doc=docs_dir / "SPRINT_13_REVIEW_ONLY_ROOKIE_BOARD.md",
    )
    _write_csv(paths.prospect_review_rows, PROSPECT_REVIEW_HEADER, result.prospect_rows)
    _write_csv(paths.prospect_component_rows, COMPONENT_HEADER, result.prospect_component_rows)
    _write_csv(paths.prospect_receipts, RECEIPT_HEADER, result.prospect_receipt_rows)
    _write_csv(paths.prospect_warnings, WARNING_HEADER, result.prospect_warning_rows)
    _write_csv(paths.pick_baselines, PICK_BASELINE_HEADER, result.pick_rows)
    _write_csv(paths.dynasty_review_rows, DYNASTY_REVIEW_HEADER, result.dynasty_rows)
    _write_csv(paths.dynasty_component_rows, COMPONENT_HEADER, result.dynasty_component_rows)
    _write_csv(paths.dynasty_receipts, RECEIPT_HEADER, result.dynasty_receipt_rows)
    _write_csv(paths.dynasty_warnings, WARNING_HEADER, result.dynasty_warning_rows)
    _write_doc(paths.sprint12_doc, _sprint12_doc(result, paths))
    _write_doc(paths.sprint13_doc, _sprint13_doc(result, paths))
    return paths


def _assert_prospect_contract() -> None:
    checks = (
        ("row_metadata", "formula_identity_admitted|position|draft_year|college|nfl_team"),
        ("factual_evidence_json", "college_production_summary"),
        ("factual_evidence_json", "college_season_latest"),
        ("factual_evidence_json", "college_targets_latest"),
        ("derived_evidence_json", "college_market_share"),
        ("derived_evidence_json", "college_team_context"),
        ("prospect_prior_evidence_json", "recruiting_profile"),
        ("prospect_prior_evidence_json", "workout_profile"),
        ("source_status_json", "source_status_json"),
        ("receipt_pointers_json", "receipt_pointers_json"),
    )
    for lane, path in checks:
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=ADMITTED_PROSPECT_MATRIX,
            allowed_lane=lane,
            allowed_field_or_json_path=path,
            private_value=lane not in {"source_status_json", "receipt_pointers_json"},
        )
    assert_formula_field_allowed(
        module_name="rookie_context_review",
        allowed_input_file=ADMITTED_PROSPECT_MATRIX,
        allowed_lane="context_fields_json",
        allowed_field_or_json_path="nfl_depth_chart",
        private_value=False,
    )
    assert_formula_field_allowed(
        module_name="prospect_prior",
        allowed_input_file=ROOKIE_AGE_SOURCE,
        allowed_lane="rookie_age_intake_csv",
        allowed_field_or_json_path="age_years_decimal|age_total_months",
        private_value=True,
    )
    assert_formula_field_allowed(
        module_name="prospect_prior",
        allowed_input_file=DRAFT_CAPITAL_SOURCE,
        allowed_lane="rookie_draft_capital_csv",
        allowed_field_or_json_path="round|overall_pick|draft_day",
        private_value=True,
    )


def _prospect_value_row(
    row: dict[str, str],
    confidence: dict[str, str],
    age_row: dict[str, str],
    draft_capital_row: dict[str, str],
) -> dict[str, object]:
    key = row["canonical_prospect_key"]
    name = row["prospect_name"]
    position = row["position"]
    factual = _json(row.get("factual_evidence_json"))
    derived = _json(row.get("derived_evidence_json"))
    prior = _json(row.get("prospect_prior_evidence_json"))
    context = _json(row.get("context_fields_json"))
    receipts = _json(row.get("receipt_pointers_json"))
    production = _production_score(position, factual)
    market_share = _market_share_score(position, derived)
    draft_capital = _draft_capital_score(draft_capital_row)
    athletic = _athletic_score(position, prior)
    recruiting = _recruiting_score(prior)
    age_lifecycle = _age_lifecycle_score(position, age_row)
    components = {
        "production": (production, 0.30),
        "market_share": (market_share, 0.20),
        "draft_capital": (draft_capital, 0.25),
        "athletic_prior": (athletic, 0.12),
        "recruiting_prior": (recruiting, 0.05),
        "age_lifecycle": (age_lifecycle, 0.08),
    }
    available = {name_: value for name_, value in components.items() if value[0] is not None}
    core_available = {
        name_: value for name_, value in available.items() if name_ != "age_lifecycle"
    }
    base_raw = _weighted_score(available) if core_available else None
    raw, balance_labels = _rookie_formula_balance_adjustment(
        position=position,
        base_score=base_raw,
        production=production,
        market_share=market_share,
        draft_capital=draft_capital,
        athletic=athletic,
        draft_capital_row=draft_capital_row,
    )
    confidence_cap = _float(confidence.get("confidence_cap"), 0.78) or 0.78
    score = round(raw * confidence_cap, 4) if raw is not None else ""
    landing = _landing_context(context)
    warnings = _prospect_warning_flags(row, confidence, components, landing, balance_labels)
    review_row = {
        "canonical_prospect_key": key,
        "prospect_name": name,
        "normalized_player_name": row.get("normalized_player_name", ""),
        "position": position,
        "college": row.get("college", ""),
        "nfl_team": row.get("nfl_team", ""),
        "draft_year": row.get("draft_year", ""),
        "prospect_private_value_review_score": score,
        "confidence_cap": confidence_cap,
        "confidence_status": confidence.get("confidence_status", ""),
        "production_score": "" if production is None else production,
        "market_share_score": "" if market_share is None else market_share,
        "draft_capital_score": "" if draft_capital is None else draft_capital,
        "athletic_prior_score": "" if athletic is None else athletic,
        "recruiting_prior_score": "" if recruiting is None else recruiting,
        "age_lifecycle_score": "" if age_lifecycle is None else age_lifecycle,
        "age_years_decimal": age_row.get("age_years_decimal", ""),
        "rookie_formula_balance_label": "|".join(balance_labels),
        "landing_context_review": landing,
        "component_weight_available": round(sum(v[1] for v in available.values()), 4),
        "allowed_use": "review_only_prospect_private_value_not_final_rookie_board",
        "blocked_use": "do_not_use_as_final_rookie_draft_recommendation",
        "warning_flags": "|".join(warnings),
        "formula_version": SPRINT_12_13_VERSION,
    }
    component_rows = tuple(
        _component(
            key,
            name,
            "current_prospect",
            "prospect_prior",
            component_name,
            "" if value is None else value,
            value,
            weight,
            "formula_admitted_after_validation",
            _component_source_file(component_name),
            _component_lane(component_name),
            _component_path(component_name),
            "missing_prospect_component" if value is None else "",
        )
        for component_name, (value, weight) in components.items()
    ) + tuple(
        _component(
            key,
            name,
            "current_prospect",
            "formula_guardrail",
            "rookie_formula_balance_adjustment",
            "|".join(balance_labels),
            None,
            None,
            "formula_guardrail_review_only",
            "docs/model_v4/MODEL_V4_3_3_ROOKIE_FORMULA_BALANCE_REPAIR.md",
            "formula_guardrail",
            "rookie_formula_balance_label",
            "",
        )
        for _ in ([None] if balance_labels else [])
    )
    receipt_rows = _prospect_receipts(key, name, receipts)
    warning_rows = tuple(
        _warning(
            key,
            name,
            "current_prospect",
            position,
            "prospect_value",
            warning,
            "Review before using in any rookie board or dynasty asset table.",
        )
        for warning in warnings
    )
    return {
        "review_row": review_row,
        "component_rows": component_rows,
        "receipt_rows": receipt_rows,
        "warning_rows": warning_rows,
    }


def _production_score(position: str, factual: dict[str, Any]) -> float | None:
    summary = _dict(factual.get("college_production_summary"))
    latest = _dict(factual.get("college_season_latest"))
    if position == "QB":
        passing = _dict(summary.get("passing"))
        rushing = _dict(summary.get("rushing"))
        return _avg(
            _norm(passing.get("max_passing_yard_share"), 0.9, already_ratio=True),
            _norm(passing.get("max_passing_td_share"), 0.9, already_ratio=True),
            _norm(latest.get("passing_yards") or latest.get("passing_yds"), 4200),
            _norm(rushing.get("career_yards"), 1200),
            weights=(0.35, 0.25, 0.25, 0.15),
        )
    if position == "RB":
        rushing = _dict(summary.get("rushing"))
        receiving = _dict(summary.get("receiving"))
        return _avg(
            _norm(rushing.get("max_rushing_yard_share"), 0.45, already_ratio=True),
            _norm(rushing.get("max_rushing_td_share"), 0.55, already_ratio=True),
            _norm(rushing.get("career_yards"), 3500),
            _norm(receiving.get("career_yards"), 900),
            weights=(0.35, 0.20, 0.25, 0.20),
        )
    if position == "WR":
        receiving = _dict(summary.get("receiving"))
        targets = _dict(factual.get("college_targets_latest"))
        return _avg(
            _norm(receiving.get("max_receiving_yard_share"), 0.4, already_ratio=True),
            _norm(receiving.get("max_reception_share"), 0.35, already_ratio=True),
            _norm(receiving.get("career_yards"), 3200),
            _norm(targets.get("targets"), 160),
            weights=(0.35, 0.25, 0.25, 0.15),
        )
    receiving = _dict(summary.get("receiving"))
    targets = _dict(factual.get("college_targets_latest"))
    return _avg(
        _norm(receiving.get("max_receiving_yard_share"), 0.25, already_ratio=True),
        _norm(receiving.get("max_reception_share"), 0.25, already_ratio=True),
        _norm(receiving.get("career_yards"), 2200),
        _norm(targets.get("targets"), 120),
        weights=(0.30, 0.25, 0.25, 0.20),
    )


def _market_share_score(position: str, derived: dict[str, Any]) -> float | None:
    share = _dict(derived.get("college_market_share"))
    if position == "QB":
        passing = _dict(share.get("passing"))
        rushing = _dict(share.get("rushing"))
        return _avg(
            _norm(passing.get("passing_yard_share"), 0.85, already_ratio=True),
            _norm(passing.get("passing_td_share"), 0.85, already_ratio=True),
            _norm(rushing.get("rushing_yard_share"), 0.18, already_ratio=True),
            weights=(0.45, 0.35, 0.20),
        )
    if position == "RB":
        rushing = _dict(share.get("rushing"))
        receiving = _dict(share.get("receiving"))
        return _avg(
            _norm(rushing.get("rushing_yard_share"), 0.45, already_ratio=True),
            _norm(rushing.get("rushing_td_share"), 0.55, already_ratio=True),
            _norm(receiving.get("receiving_yard_share"), 0.12, already_ratio=True),
            weights=(0.45, 0.35, 0.20),
        )
    receiving = _dict(share.get("receiving"))
    return _avg(
        _norm(receiving.get("receiving_yard_share"), 0.35, already_ratio=True),
        _norm(receiving.get("reception_share"), 0.32, already_ratio=True),
        _norm(receiving.get("receiving_td_share"), 0.4, already_ratio=True),
        weights=(0.45, 0.35, 0.20),
    )


def _draft_capital_score(draft_capital_row: dict[str, str]) -> float | None:
    pick = _float(draft_capital_row.get("overall_pick"))
    if pick is None:
        return None
    if pick <= 32:
        score = 100 - ((pick - 1) * (22 / 31))
    elif pick <= 100:
        score = 78 - ((pick - 32) * (28 / 68))
    else:
        score = 50 - ((pick - 100) * (45 / 160))
    return round(_clamp(score), 4)


def _rookie_formula_balance_adjustment(
    *,
    position: str,
    base_score: float | None,
    production: float | None,
    market_share: float | None,
    draft_capital: float | None,
    athletic: float | None,
    draft_capital_row: dict[str, str],
) -> tuple[float | None, tuple[str, ...]]:
    if base_score is None:
        return None, ()

    adjusted = base_score
    labels: list[str] = []
    pick = _float(draft_capital_row.get("overall_pick"))
    if pick is None or draft_capital is None:
        labels.append("source_shape_warning:missing_draft_capital")
        return adjusted, tuple(labels)

    production_market = _avg(production, market_share, weights=(0.55, 0.45))
    exceptional_profile = (
        production_market is not None
        and production_market >= 86.0
        and (athletic is None or athletic >= 75.0)
    )

    if pick <= 32:
        anchor_ratio = {"RB": 0.72, "WR": 0.70, "TE": 0.58, "QB": 0.48}.get(position, 0.62)
        anchor_floor = draft_capital * anchor_ratio
        if adjusted < anchor_floor:
            adjusted = anchor_floor
            labels.append("draft_capital_anchor_warning:first_round_floor_applied")
        elif production_market is not None and production_market > draft_capital + 8:
            labels.append("model_edge_weirdness:production_exceeds_first_round_capital")

    if pick > 100 and production_market is not None and production_market > draft_capital + 18:
        if exceptional_profile:
            labels.append("model_edge_weirdness:day_three_exceptional_profile")
        else:
            adjusted = min(adjusted, 58.0)
            labels.append("draft_capital_anchor_warning:day_three_skepticism_cap")

    if position == "TE":
        if pick > 32:
            adjusted = min(adjusted, 56.0)
            labels.append("no_premium_te_cap_warning:non_first_round_te_cap")
        elif adjusted > 62.0:
            adjusted = 62.0
            labels.append("no_premium_te_cap_warning:first_round_te_no_premium_cap")

    if position == "QB" and pick > 8:
        adjusted = min(adjusted, 58.0)
        labels.append("source_shape_warning:one_qb_qb_scarcity_cap")

    if labels:
        return round(adjusted, 4), tuple(dict.fromkeys(labels))
    return base_score, ()


def _athletic_score(position: str, prior: dict[str, Any]) -> float | None:
    workout = _dict(prior.get("workout_profile"))
    if not workout:
        return None
    values: list[float | None]
    if position in {"RB", "WR"}:
        values = [
            _float(workout.get("forty_pct")),
            _float(workout.get("broad_pct")),
            _float(workout.get("vertical_pct")),
            _float(workout.get("cone_pct")),
        ]
    elif position == "TE":
        values = [
            _float(workout.get("forty_pct")),
            _float(workout.get("broad_pct")),
            _float(workout.get("vertical_pct")),
            _norm(workout.get("weight"), 260),
        ]
    else:
        values = [_float(workout.get("forty_pct")), _float(workout.get("cone_pct"))]
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def _recruiting_score(prior: dict[str, Any]) -> float | None:
    recruiting = _dict(prior.get("recruiting_profile"))
    rating = _float(recruiting.get("rating"))
    stars = _float(recruiting.get("stars"))
    return _avg(_norm(rating, 1.0), _norm(stars, 5.0), weights=(0.7, 0.3))


def _age_lifecycle_score(position: str, age_row: dict[str, str]) -> float | None:
    age = _float(age_row.get("age_years_decimal"))
    if age is None:
        return None
    if position == "RB":
        return _piecewise_age_score(
            age,
            ideal_age=21.5,
            soft_start=22.5,
            hard_start=24.5,
            floor=45.0,
        )
    if position == "WR":
        return _piecewise_age_score(
            age,
            ideal_age=21.7,
            soft_start=23.2,
            hard_start=24.8,
            floor=55.0,
        )
    if position == "TE":
        return _piecewise_age_score(
            age,
            ideal_age=22.0,
            soft_start=24.0,
            hard_start=25.5,
            floor=60.0,
        )
    if position == "QB":
        return _piecewise_age_score(
            age,
            ideal_age=22.4,
            soft_start=24.0,
            hard_start=25.5,
            floor=60.0,
        )
    return None


def _piecewise_age_score(
    age: float,
    *,
    ideal_age: float,
    soft_start: float,
    hard_start: float,
    floor: float,
) -> float:
    if age <= ideal_age:
        return 100.0
    if age <= soft_start:
        return round(100.0 - ((age - ideal_age) / (soft_start - ideal_age)) * 10.0, 4)
    if age <= hard_start:
        return round(90.0 - ((age - soft_start) / (hard_start - soft_start)) * 25.0, 4)
    return max(floor, round(65.0 - (age - hard_start) * 12.0, 4))


def _landing_context(context: dict[str, Any]) -> str:
    depth = _dict(context.get("nfl_depth_chart"))
    if not depth:
        return "landing_context_missing"
    rank = depth.get("depth_rank")
    team = depth.get("team") or ""
    return f"depth_rank={rank};team={team};review_context_only"


def _prospect_warning_flags(
    row: dict[str, str],
    confidence: dict[str, str],
    components: dict[str, tuple[float | None, float]],
    landing: str,
    balance_labels: tuple[str, ...],
) -> tuple[str, ...]:
    warnings = [
        *_split_flags(row.get("warning_flags")),
        *_split_flags(confidence.get("cap_reasons")),
    ]
    for name, (value, _) in components.items():
        if value is None:
            warnings.append(f"missing_{name}_component")
    if landing == "landing_context_missing":
        warnings.append("missing_landing_context_review")
    warnings.extend(label.split(":", 1)[0] for label in balance_labels)
    warnings.append("market_context_excluded_from_private_value")
    return tuple(dict.fromkeys(warnings))


def _weighted_score(values: dict[str, tuple[float | None, float]]) -> float | None:
    total_weight = sum(weight for _, weight in values.values())
    if total_weight <= 0:
        return None
    weighted_total = sum((score or 0.0) * weight for score, weight in values.values())
    return round(weighted_total / total_weight, 4)


def _component_lane(component_name: str) -> str:
    if component_name in {"rookie_formula_balance_adjustment"}:
        return "formula_guardrail"
    if component_name in {"age_lifecycle"}:
        return "rookie_age_intake_csv"
    if component_name in {"draft_capital"}:
        return "rookie_draft_capital_csv"
    if component_name in {"production"}:
        return "factual_evidence_json"
    if component_name in {"market_share"}:
        return "derived_evidence_json"
    return "prospect_prior_evidence_json"


def _component_path(component_name: str) -> str:
    return {
        "production": "college_production_summary|college_season_latest|college_targets_latest",
        "market_share": "college_market_share",
        "draft_capital": "rookie_draft_capital_2026.overall_pick",
        "athletic_prior": "workout_profile",
        "recruiting_prior": "recruiting_profile",
        "age_lifecycle": "rookie_age_2026.age_years_decimal",
        "rookie_formula_balance_adjustment": "rookie_formula_balance_label",
    }[component_name]


def _component_source_file(component_name: str) -> str:
    if component_name == "age_lifecycle":
        return ROOKIE_AGE_SOURCE
    if component_name == "draft_capital":
        return DRAFT_CAPITAL_ROWS.as_posix()
    return ADMITTED_PROSPECT_MATRIX


def _prospect_receipts(
    key: str,
    name: str,
    receipts: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    groups = (
        ("college_production", "factual_evidence_json", "college_production_summary"),
        ("college_targets", "factual_evidence_json", "college_targets_latest"),
        ("college_market_share", "derived_evidence_json", "college_market_share"),
        ("draft_capital", "rookie_draft_capital_csv", "overall_pick"),
        ("workouts", "prospect_prior_evidence_json", "workout_profile"),
        ("recruiting_profile", "prospect_prior_evidence_json", "recruiting_profile"),
        ("rookie_age", "rookie_age_intake_csv", "age_years_decimal"),
    )
    return tuple(
        _receipt(
            key,
            name,
            "current_prospect",
            "prospect_prior",
            group,
            str(receipts.get(group) or _receipt_source_file(group)),
            "formula_admitted_after_validation",
            _receipt_source_file(group),
            lane,
            path,
        )
        for group, lane, path in groups
    )


def _receipt_source_file(group: str) -> str:
    if group == "rookie_age":
        return ROOKIE_AGE_SOURCE
    return ADMITTED_PROSPECT_MATRIX


def _pick_baselines() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for season, season_multiplier in ((2026, 1.0), (2027, 1.08)):
        for round_ in range(1, 5):
            for slot in range(1, 11):
                base = max(8.0, 100.0 - ((round_ - 1) * 19.0) - ((slot - 1) * 3.2))
                score = round(min(100.0, base * season_multiplier), 4)
                rows.append(
                    {
                        "pick_asset_key": f"pick:{season}:{round_}.{slot:02d}",
                        "season": season,
                        "round": round_,
                        "pick_slot": slot,
                        "pick_label": f"{season} {round_}.{slot:02d}",
                        "pick_value_review_score": score,
                        "tier_label": _pick_tier(round_, slot),
                        "confidence_status": "review_only_pick_baseline_no_market_input",
                        "allowed_use": "review_only_pick_value_baseline_not_trade_recommendation",
                        "warning_flags": "heuristic_pick_curve_requires_audit",
                        "formula_version": SPRINT_12_13_VERSION,
                    }
                )
    return tuple(rows)


def _pick_tier(round_: int, slot: int) -> str:
    if round_ == 1 and slot <= 3:
        return "early_first"
    if round_ == 1 and slot <= 6:
        return "mid_first"
    if round_ == 1:
        return "late_first"
    if round_ == 2:
        return "second_round"
    return "depth_pick"


def _current_asset_rows(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "asset_key": row["canonical_player_key"],
            "asset_name": row["player_name"],
            "asset_type": "current_player",
            "position": row["position"],
            "team_or_college": row["nfl_team"],
            "dynasty_asset_value_review_score": row["checkpoint_review_score"],
            "source_value_score": row["position_specific_review_score"],
            "confidence_cap": row["confidence_cap"],
            "value_source_layer": "phase_11g_current_player_value_checkpoint",
            "allowed_use": "review_only_unified_asset_value_not_final_ranking",
            "blocked_use": "do_not_use_as_final_ranking_or_roster_recommendation",
            "warning_flags": row["warning_flags"],
            "formula_version": SPRINT_12_13_VERSION,
        }
        for row in rows
    )


def _prospect_asset_rows(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "asset_key": row["canonical_prospect_key"],
            "asset_name": row["prospect_name"],
            "asset_type": "current_prospect",
            "position": row["position"],
            "team_or_college": row["college"],
            "dynasty_asset_value_review_score": row["prospect_private_value_review_score"],
            "source_value_score": row["prospect_private_value_review_score"],
            "confidence_cap": row["confidence_cap"],
            "value_source_layer": "sprint_13_review_only_prospect_value",
            "allowed_use": "review_only_unified_asset_value_not_final_ranking",
            "blocked_use": "do_not_use_as_final_rookie_draft_recommendation",
            "warning_flags": row["warning_flags"],
            "formula_version": SPRINT_12_13_VERSION,
        }
        for row in rows
    )


def _pick_asset_rows(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "asset_key": row["pick_asset_key"],
            "asset_name": row["pick_label"],
            "asset_type": "rookie_pick",
            "position": "",
            "team_or_college": "",
            "dynasty_asset_value_review_score": row["pick_value_review_score"],
            "source_value_score": row["pick_value_review_score"],
            "confidence_cap": "",
            "value_source_layer": "sprint_12_review_only_pick_baseline",
            "allowed_use": "review_only_unified_asset_value_not_final_ranking",
            "blocked_use": "do_not_use_as_final_pick_trade_or_draft_recommendation",
            "warning_flags": row["warning_flags"],
            "formula_version": SPRINT_12_13_VERSION,
        }
        for row in rows
    )


def _current_asset_components(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _component(
            row.get("canonical_player_key", ""),
            row.get("player_name", ""),
            "current_player",
            row.get("component_layer", "current_player_value"),
            row.get("component_name", ""),
            row.get("component_value", ""),
            _float(row.get("normalized_score")),
            _float(row.get("component_weight")),
            row.get("source_status", ""),
            row.get("source_file", ""),
            "",
            "",
            row.get("component_warning", ""),
        )
        for row in rows
    )


def _prospect_asset_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return rows


def _pick_asset_components(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _component(
            str(row["pick_asset_key"]),
            str(row["pick_label"]),
            "rookie_pick",
            "pick_value_baseline",
            "heuristic_pick_curve",
            row["tier_label"],
            _float(row["pick_value_review_score"]),
            None,
            "review_only_heuristic_requires_audit",
            "local_generated_review_only_pick_baseline",
            "pick_baseline",
            "season|round|pick_slot",
            "heuristic_pick_curve_requires_audit",
        )
        for row in rows
    )


def _current_asset_receipts(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(
            row.get("canonical_player_key", ""),
            row.get("player_name", ""),
            "current_player",
            row.get("receipt_layer", "current_player_value"),
            row.get("feature_group", ""),
            row.get("receipt_pointer", ""),
            row.get("source_status", ""),
            row.get("allowed_input_file", ""),
            row.get("allowed_lane", ""),
            row.get("allowed_field_or_json_path", ""),
        )
        for row in rows
    )


def _prospect_asset_receipts(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return rows


def _pick_asset_receipts(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(
            str(row["pick_asset_key"]),
            str(row["pick_label"]),
            "rookie_pick",
            "pick_value_baseline",
            "heuristic_pick_curve",
            "local_generated_review_only_pick_baseline",
            "review_only_heuristic_requires_audit",
            "local_generated_review_only_pick_baseline",
            "pick_baseline",
            "season|round|pick_slot",
        )
        for row in rows
    )


def _current_asset_warnings(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            row.get("entity_key", ""),
            row.get("player_name", ""),
            "current_player",
            row.get("position", ""),
            "current_player_value",
            row.get("warning_code", ""),
            row.get("next_action", ""),
        )
        for row in rows
    )


def _prospect_asset_warnings(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return rows


def _pick_asset_warnings(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            str(row["pick_asset_key"]),
            str(row["pick_label"]),
            "rookie_pick",
            "",
            "pick_value_baseline",
            "heuristic_pick_curve_requires_audit",
            "Do not use as a trade recommendation without audit.",
        )
        for row in rows
    )


def _dynasty_sanity_warnings(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    names = {str(row["asset_name"]) for row in rows}
    required = {
        "Christian McCaffrey",
        "Lamar Jackson",
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "2026 1.01",
        "2027 1.01",
    }
    warnings = [
        _warning(
            "sprint_12_13_sanity",
            "Sprint 12/13",
            "all",
            "",
            "sanity_fixture",
            "review_only_no_final_recommendations",
            "Unified table is review-only and not a final decision layer.",
        )
    ]
    for name in sorted(required):
        warnings.append(
            _warning(
                f"sprint_12_13_sanity:{name}",
                name,
                "all",
                "",
                "sanity_fixture",
                "required_asset_present" if name in names else "required_asset_missing",
                f"{name} {'present' if name in names else 'missing'} in unified review table.",
            )
        )
    return tuple(warnings)


def _component(
    key: str,
    name: str,
    entity_type: str,
    layer: str,
    component_name: str,
    component_value: object,
    normalized_score: float | None,
    weight: float | None,
    source_status: str,
    allowed_input_file: str,
    allowed_lane: str,
    allowed_path: str,
    warning: str,
) -> dict[str, object]:
    contribution = (
        round(normalized_score * weight, 4)
        if normalized_score is not None and weight is not None
        else ""
    )
    return {
        "entity_key": key,
        "entity_name": name,
        "entity_type": entity_type,
        "component_layer": layer,
        "component_name": component_name,
        "component_value": component_value,
        "normalized_score": "" if normalized_score is None else normalized_score,
        "component_weight": "" if weight is None else weight,
        "weighted_contribution": contribution,
        "source_status": source_status,
        "allowed_input_file": allowed_input_file,
        "allowed_lane": allowed_lane,
        "allowed_field_or_json_path": allowed_path,
        "component_warning": warning,
        "formula_version": SPRINT_12_13_VERSION,
    }


def _receipt(
    key: str,
    name: str,
    entity_type: str,
    layer: str,
    feature_group: str,
    pointer: str,
    source_status: str,
    input_file: str,
    lane: str,
    path: str,
) -> dict[str, object]:
    return {
        "entity_key": key,
        "entity_name": name,
        "entity_type": entity_type,
        "receipt_layer": layer,
        "feature_group": feature_group,
        "receipt_pointer": pointer,
        "source_status": source_status,
        "allowed_input_file": input_file,
        "allowed_lane": lane,
        "allowed_field_or_json_path": path,
        "receipt_requirement": "Receipt pointer required before formula promotion.",
        "formula_version": SPRINT_12_13_VERSION,
    }


def _warning(
    key: str,
    name: str,
    entity_type: str,
    position: str,
    layer: str,
    code: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "entity_key": key,
        "entity_name": name,
        "entity_type": entity_type,
        "position": position,
        "warning_layer": layer,
        "warning_type": "review",
        "severity": "review",
        "warning_code": code,
        "warning_detail": code.replace("_", " "),
        "next_action": next_action,
        "formula_version": SPRINT_12_13_VERSION,
    }


def _sprint12_doc(result: Sprint1213ReviewResult, paths: Sprint1213ReviewPaths) -> str:
    return "\n".join(
        [
            "# Sprint 12 Review-Only Dynasty Value",
            "",
            "Sprint 12 builds a unified review-only asset table. It is not a final "
            "dynasty ranking, trade board, cut list, or app-promotion surface.",
            "",
            "## Outputs",
            "",
            f"- `{paths.dynasty_review_rows}`",
            f"- `{paths.dynasty_component_rows}`",
            f"- `{paths.dynasty_receipts}`",
            f"- `{paths.dynasty_warnings}`",
            f"- `{paths.pick_baselines}`",
            "",
            "## Summary",
            "",
            f"- Unified asset rows: {result.summary['dynasty_asset_rows']}",
            f"- Prospect rows: {result.summary['prospect_rows']}",
            f"- Pick baseline rows: {result.summary['pick_rows']}",
            "- Market/projection/ADP rows used for private value: 0",
            "",
            "## Safety",
            "",
            "Current player, prospect, and pick values remain separable by "
            "`value_source_layer`. Pick values are heuristic baselines requiring audit.",
        ]
    ) + "\n"


def _sprint13_doc(result: Sprint1213ReviewResult, paths: Sprint1213ReviewPaths) -> str:
    return "\n".join(
        [
            "# Sprint 13 Review-Only Rookie Board",
            "",
            "Sprint 13 creates a review-only prospect private-value scaffold from "
            "admitted prospect evidence. Market, ADP, rankings, mock drafts, and "
            "big boards are excluded from private value.",
            "",
            "## Outputs",
            "",
            f"- `{paths.prospect_review_rows}`",
            f"- `{paths.prospect_component_rows}`",
            f"- `{paths.prospect_receipts}`",
            f"- `{paths.prospect_warnings}`",
            "",
            "## Summary",
            "",
            f"- Prospect rows: {result.summary['prospect_rows']}",
            "- Uses admitted prospect matrix only.",
            "- Confidence caps are applied from Phase 11F metadata.",
            "- This is not a final rookie draft recommendation surface.",
        ]
    ) + "\n"


def _norm(value: object, ceiling: float, *, already_ratio: bool = False) -> float | None:
    parsed = _float(value)
    if parsed is None or ceiling <= 0:
        return None
    if already_ratio:
        parsed = max(0.0, parsed)
    return round(max(0.0, min(100.0, (parsed / ceiling) * 100.0)), 4)


def _clamp(value: float, floor: float = 0.0, ceiling: float = 100.0) -> float:
    return max(floor, min(ceiling, value))


def _avg(*values: float | None, weights: tuple[float, ...]) -> float | None:
    present = [
        (value, weight)
        for value, weight in zip(values, weights, strict=False)
        if value is not None
    ]
    total_weight = sum(weight for _, weight in present)
    if total_weight <= 0:
        return None
    return round(sum(value * weight for value, weight in present) / total_weight, 4)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _json(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _split_flags(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(flag.strip() for flag in str(value).split("|") if flag.strip())


def _index(rows: tuple[dict[str, str], ...], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def _normalize_name(value: str) -> str:
    lowered = value.lower().strip()
    for token in (" jr.", " sr.", " ii", " iii", " iv"):
        lowered = lowered.replace(token, "")
    return re.sub(r"[^a-z0-9]+", "", lowered)


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
