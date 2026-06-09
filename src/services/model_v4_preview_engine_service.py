from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.model_v4_component_calculator_service import (
    ModelV4ComponentReceipt,
    calculate_all_model_v4_components,
    load_model_v4_formula_config,
)
from src.services.truth_set_first_down_projection_estimator_service import (
    FirstDownEstimatorResult,
    build_first_down_estimator_preview,
    write_first_down_estimator_outputs,
)

DEFAULT_TRUTH_SET_PATH = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_FORMULA_CONFIG_PATH = Path("docs/model_v4/MODEL_V4_FORMULA_CONFIG.json")
DEFAULT_V3_REPORT_ROOT = Path("local_exports/model_v4/source_reports")
DEFAULT_PROJECTION_PATH = Path("local_exports/truth_set_lab/v1/source_clean/projections.csv")
DEFAULT_YOUNG_PRIOR_PATH = Path(
    "local_exports/truth_set_lab/v2/reports/young_bridge_prior_preview.csv"
)
DEFAULT_V3_2_ROOT = Path(
    "local_exports/truth_set_lab/v3_2/promoted_review_models"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4")

V4_PREVIEW_OUTPUT_HEADER = (
    "player",
    "position",
    "nfl_team",
    "lifecycle",
    "truth_set_group",
    "source_priority",
    "dynasty_asset_value",
    "value_basis",
    "scored_component_weight",
    "missing_component_weight",
    "missing_value_components",
    "confidence",
    "confidence_label",
    "component_scores",
    "component_contributions",
    "review_warnings",
    "unavailable_sections",
    "review_status",
    "formula_version",
    "preview_engine_version",
)

V4_COMPONENT_HEADER = (
    "player",
    "position",
    "component",
    "normalized_score",
    "weight",
    "contribution",
    "source_status",
    "raw_fields_used",
    "warning",
    "unavailable_reason",
    "review_only",
)

V4_RECEIPT_HEADER = (
    "player",
    "position",
    "component",
    "raw_fields_used",
    "raw_values",
    "normalized_score",
    "source_status",
    "contribution",
    "weight",
    "warning",
    "unavailable_reason",
    "review_only",
)

V4_SOURCE_COVERAGE_HEADER = (
    "player",
    "position",
    "section",
    "source_status",
    "coverage_status",
    "warning",
    "unavailable_reason",
)

V4_WARNING_HEADER = (
    "player",
    "position",
    "component",
    "warning",
    "severity",
    "detail",
)

V4_SUMMARY_HEADER = ("metric", "value")

MODEL_V4_PREVIEW_ENGINE_VERSION = "model_v4_preview_engine_review_only_0.1.0"


@dataclass(frozen=True)
class ModelV4PreviewEngineResult:
    output_root: Path
    preview_outputs_path: Path
    normalized_components_path: Path
    receipts_path: Path
    source_coverage_path: Path
    warnings_path: Path
    summary_path: Path
    summary: dict[str, object]


def build_model_v4_preview(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET_PATH,
    formula_config_path: str | Path = DEFAULT_FORMULA_CONFIG_PATH,
    v3_report_root: str | Path = DEFAULT_V3_REPORT_ROOT,
    projection_path: str | Path = DEFAULT_PROJECTION_PATH,
    young_prior_path: str | Path = DEFAULT_YOUNG_PRIOR_PATH,
    v3_2_root: str | Path = DEFAULT_V3_2_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    preview_id: str = "review_only_latest",
    computed_at: str | None = None,
) -> ModelV4PreviewEngineResult:
    formula_config = load_model_v4_formula_config(formula_config_path)
    truth_rows = _read_dicts(Path(truth_set_path))
    report_root = Path(v3_report_root)
    production_rows = _latest_by_key(
        _read_optional(report_root / "truth_set_v3_production_player_season.csv")
    )
    usage_rows = _latest_by_key(
        _read_optional(report_root / "truth_set_v3_usage_player_season.csv")
    )
    snap_rows = _latest_by_key(
        _read_optional(report_root / "truth_set_v3_snap_share_player_season.csv")
    )
    projection_rows = _by_key(_read_optional(Path(projection_path)))
    first_down_estimator = _build_first_down_estimator_result(
        projection_path=Path(projection_path),
        historical_stats_path=report_root / "truth_set_v3_production_player_season.csv",
    )
    first_down_estimate_rows = _by_key(
        list(first_down_estimator.estimate_rows) if first_down_estimator else []
    )
    young_rows = _by_key(_read_optional(Path(young_prior_path)))
    active_context_rows = _by_key(
        _read_optional(latest_v3_2_promoted_root(v3_2_root) / "stats_first_normalized_features.csv")
    )

    output_rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []

    for truth in truth_rows:
        key = _player_key(truth)
        calculation_row = _calculation_row(
            truth,
            production_rows.get(key),
            usage_rows.get(key),
            snap_rows.get(key),
            projection_rows.get(key),
            first_down_estimate_rows.get(key),
            young_rows.get(key),
            active_context_rows.get(key),
        )
        receipts = calculate_all_model_v4_components(
            calculation_row,
            position=str(truth.get("position") or ""),
            season=2026,
            config=formula_config,
        )
        player = str(truth.get("player_name") or "")
        position = str(truth.get("position") or "")
        output_rows.append(
            _preview_output_row(
                truth,
                receipts,
                formula_version=str(formula_config["formula_version"]),
                formula_config=formula_config,
            )
        )
        component_rows.extend(_component_rows(player, position, receipts))
        receipt_rows.extend(_receipt_rows(player, position, receipts))
        coverage_rows.extend(_source_coverage_rows(player, position, receipts))
        warning_rows.extend(_warning_rows(player, position, receipts))

    root = Path(output_root) / preview_id
    root.mkdir(parents=True, exist_ok=True)
    preview_outputs_path = root / "v4_preview_outputs.csv"
    normalized_components_path = root / "v4_normalized_component_rows.csv"
    receipts_path = root / "v4_receipt_rows.csv"
    source_coverage_path = root / "v4_source_coverage_rows.csv"
    warnings_path = root / "v4_warning_rows.csv"
    summary_path = root / "v4_preview_summary.csv"
    if first_down_estimator:
        write_first_down_estimator_outputs(
            estimate_path=root / "v4_first_down_projection_estimates.csv",
            rate_path=root / "v4_first_down_projection_rates.csv",
            summary_path=root / "v4_first_down_projection_summary.csv",
            result=first_down_estimator,
        )

    summary = {
        "preview_id": preview_id,
        "computed_at": computed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "review_status": "review_only",
        "formula_version": formula_config["formula_version"],
        "preview_engine_version": MODEL_V4_PREVIEW_ENGINE_VERSION,
        "truth_set_players": len(truth_rows),
        "preview_output_rows": len(output_rows),
        "component_rows": len(component_rows),
        "receipt_rows": len(receipt_rows),
        "source_coverage_rows": len(coverage_rows),
        "warning_rows": len(warning_rows),
        "projection_first_down_estimate_rows": (
            len(first_down_estimator.estimate_rows) if first_down_estimator else 0
        ),
        "projection_first_down_estimated_from_history_rows": (
            first_down_estimator.summary["estimated_from_history_rows"]
            if first_down_estimator
            else 0
        ),
        "projection_first_down_direct_rows": (
            first_down_estimator.summary["direct_first_down_projection_rows"]
            if first_down_estimator
            else 0
        ),
        "projection_first_down_missing_rows": (
            first_down_estimator.summary["missing_first_down_projection_rows"]
            if first_down_estimator
            else 0
        ),
        "active_rankings_overwritten": False,
        "app_promotion": False,
        "decision_ready_unlocked": False,
        "draft_ready_unlocked": False,
        "final_money_ready_unlocked": False,
    }
    _write_dicts(preview_outputs_path, V4_PREVIEW_OUTPUT_HEADER, output_rows)
    _write_dicts(normalized_components_path, V4_COMPONENT_HEADER, component_rows)
    _write_dicts(receipts_path, V4_RECEIPT_HEADER, receipt_rows)
    _write_dicts(source_coverage_path, V4_SOURCE_COVERAGE_HEADER, coverage_rows)
    _write_dicts(warnings_path, V4_WARNING_HEADER, warning_rows)
    _write_dicts(summary_path, V4_SUMMARY_HEADER, _summary_rows(summary))
    (root / "v4_preview_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ModelV4PreviewEngineResult(
        output_root=root,
        preview_outputs_path=preview_outputs_path,
        normalized_components_path=normalized_components_path,
        receipts_path=receipts_path,
        source_coverage_path=source_coverage_path,
        warnings_path=warnings_path,
        summary_path=summary_path,
        summary=summary,
    )


def latest_v3_2_promoted_root(
    root: str | Path = DEFAULT_V3_2_ROOT,
) -> Path:
    candidates = [
        path
        for path in Path(root).glob("truth_set_v3_2_promoted_review_*")
        if path.is_dir()
    ]
    if not candidates:
        return Path(root)
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _calculation_row(
    truth: dict[str, str],
    production: dict[str, str] | None,
    usage: dict[str, str] | None,
    snap: dict[str, str] | None,
    projection: dict[str, str] | None,
    first_down_estimate: dict[str, str] | None,
    young_prior: dict[str, str] | None,
    active_context: dict[str, str] | None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "player_name": truth.get("player_name", ""),
        "position": truth.get("position", ""),
        "nfl_team": truth.get("nfl_team", ""),
        "asset_lifecycle": truth.get("lifecycle_expected", ""),
    }
    if active_context:
        row.update(
            {
                "confidence": active_context.get("confidence", ""),
                "warnings": active_context.get("warnings", ""),
                "age": active_context.get("age_raw", ""),
                "injury_durability": active_context.get("injury_durability", ""),
                "role_security": active_context.get("role_security", ""),
                "draft_year": active_context.get("draft_year", ""),
                "draft_round": active_context.get("draft_round", ""),
                "draft_overall": active_context.get("draft_overall", ""),
            }
        )
    if production:
        row.update(
            _copy_fields(
                production,
                (
                    "passing_yards",
                    "passing_tds",
                    "interceptions",
                    "rushing_attempts",
                    "rushing_yards",
                    "rushing_tds",
                    "targets",
                    "receiving_yards",
                    "receiving_tds",
                    "receptions",
                    "fumbles_lost",
                    "rushing_first_downs",
                    "receiving_first_downs",
                ),
            )
        )
        row["production_source_status"] = production.get("source_status", "")
        row["first_down_source_status"] = production.get("source_status", "")
    if usage:
        row.update(
            _copy_fields(
                usage,
                (
                    "target_share",
                    "targets",
                    "team_targets",
                    "rb_carry_share",
                    "rb_target_share",
                    "rushing_attempts",
                    "team_rushing_attempts",
                    "weighted_opportunities",
                    "red_zone_carries",
                    "red_zone_targets",
                    "goal_line_carries",
                    "goal_line_targets",
                    "short_yardage_carries",
                    "games_with_usage",
                ),
            )
        )
        row["usage_source_status"] = usage.get("source_status", "")
    if snap:
        row.update(
            _copy_fields(
                snap,
                (
                    "games",
                    "games_with_offensive_snaps",
                    "offense_snaps",
                    "avg_offense_pct",
                    "avg_snap_share",
                ),
            )
        )
        row["snap_share"] = snap.get("avg_snap_share", "")
        row["offense_pct"] = snap.get("avg_offense_pct", "")
        row["snap_source_status"] = snap.get("source_status", "")
    if projection:
        if not _projection_has_raw_stats(projection):
            _add_review_gap(row, "missing_projection_data")
        row.update(
            _copy_fields(
                projection,
                (
                    "projected_games",
                    "projected_starts",
                    "projected_passing_yards",
                    "projected_passing_tds",
                    "projected_interceptions",
                    "projected_rushing_attempts",
                    "projected_rushing_yards",
                    "projected_rushing_tds",
                    "projected_targets",
                    "projected_receptions",
                    "projected_receiving_yards",
                    "projected_receiving_tds",
                    "projected_rushing_first_downs",
                    "projected_receiving_first_downs",
                    "projected_lve_points_if_calculable",
                ),
            )
        )
        row["projection_source_status"] = "projection_stat_recompute_review_only"
        row["raw_stat_projection_status"] = "independent_raw_stat_projection"
        row["recomputed_lve_projection_status"] = "recomputed_from_raw_projection_stats"
        if first_down_estimate:
            estimate_status = first_down_estimate.get(
                "first_down_estimate_status",
                "",
            )
            row["first_down_projection_status"] = estimate_status
            row["first_down_projection_rate_source_status"] = first_down_estimate.get(
                "rate_source_status",
                "",
            )
            row["first_down_projection_model_usage_status"] = first_down_estimate.get(
                "model_usage_status",
                "",
            )
            row["rushing_first_down_rate"] = first_down_estimate.get(
                "rushing_first_down_rate",
                "",
            )
            row["rushing_first_down_rate_scope"] = first_down_estimate.get(
                "rushing_first_down_rate_scope",
                "",
            )
            row["receiving_first_down_rate_basis"] = first_down_estimate.get(
                "receiving_first_down_rate_basis",
                "",
            )
            row["receiving_first_down_rate"] = first_down_estimate.get(
                "receiving_first_down_rate",
                "",
            )
            row["receiving_first_down_rate_scope"] = first_down_estimate.get(
                "receiving_first_down_rate_scope",
                "",
            )
            if estimate_status in {
                "direct_first_down_projection",
                "estimated_from_history",
            }:
                row["projected_rushing_first_downs"] = first_down_estimate.get(
                    "preview_rushing_first_downs",
                    "",
                )
                row["projected_receiving_first_downs"] = first_down_estimate.get(
                    "preview_receiving_first_downs",
                    "",
                )
            if estimate_status == "estimated_from_history":
                _add_review_gap(
                    row,
                    "projection_first_downs_estimated_from_history",
                )
            elif estimate_status == "missing_first_down_projection":
                _add_review_gap(row, "missing_first_down_projection")
            for warning in str(first_down_estimate.get("warning_flags", "")).split("|"):
                if warning:
                    _add_review_gap(row, warning)
    else:
        _add_review_gap(row, "missing_projection_data")
    if young_prior:
        row["draft_year"] = young_prior.get("draft_year", row.get("draft_year", ""))
        row["draft_round"] = young_prior.get(
            "nfl_draft_round",
            row.get("draft_round", ""),
        )
        row["draft_overall"] = young_prior.get(
            "nfl_draft_pick",
            row.get("draft_overall", ""),
        )
        row["young_nfl_bridge_prior_score"] = young_prior.get(
            "draft_capital_prior_score",
            "",
        )
    return row


def _preview_output_row(
    truth: dict[str, str],
    receipts: tuple[ModelV4ComponentReceipt, ...],
    *,
    formula_version: str,
    formula_config: dict[str, object],
) -> dict[str, object]:
    component_scores = {
        receipt.component: receipt.normalized_score
        for receipt in receipts
        if receipt.component != "confidence"
    }
    component_contributions = {
        receipt.component: receipt.contribution
        for receipt in receipts
        if receipt.component != "confidence"
    }
    warnings = _joined(
        receipt.warning for receipt in receipts if receipt.warning
    )
    unavailable = _joined(
        receipt.component
        for receipt in receipts
        if receipt.unavailable_reason and receipt.source_status != "not_applicable"
    )
    confidence = next(
        receipt for receipt in receipts if receipt.component == "confidence"
    )
    value_result = _dynasty_asset_value(
        receipts,
        str(truth.get("lifecycle_expected") or ""),
        formula_config=formula_config,
    )
    return {
        "player": truth.get("player_name", ""),
        "position": truth.get("position", ""),
        "nfl_team": truth.get("nfl_team", ""),
        "lifecycle": truth.get("lifecycle_expected", ""),
        "truth_set_group": truth.get("truth_set_group", ""),
        "source_priority": truth.get("source_priority", ""),
        "dynasty_asset_value": value_result["dynasty_asset_value"],
        "value_basis": value_result["value_basis"],
        "scored_component_weight": value_result["scored_component_weight"],
        "missing_component_weight": value_result["missing_component_weight"],
        "missing_value_components": value_result["missing_value_components"],
        "confidence": confidence.normalized_score,
        "confidence_label": confidence.raw_values.get("confidence_label", ""),
        "component_scores": json.dumps(component_scores, sort_keys=True),
        "component_contributions": json.dumps(
            component_contributions,
            sort_keys=True,
        ),
        "review_warnings": warnings,
        "unavailable_sections": unavailable,
        "review_status": "review_only",
        "formula_version": formula_version,
        "preview_engine_version": MODEL_V4_PREVIEW_ENGINE_VERSION,
    }


def _component_rows(
    player: str,
    position: str,
    receipts: tuple[ModelV4ComponentReceipt, ...],
) -> list[dict[str, object]]:
    return [
        {
            "player": player,
            "position": position,
            "component": receipt.component,
            "normalized_score": receipt.normalized_score,
            "weight": receipt.weight,
            "contribution": receipt.contribution,
            "source_status": receipt.source_status,
            "raw_fields_used": "|".join(receipt.raw_fields_used),
            "warning": receipt.warning,
            "unavailable_reason": receipt.unavailable_reason,
            "review_only": receipt.review_only,
        }
        for receipt in receipts
    ]


def _receipt_rows(
    player: str,
    position: str,
    receipts: tuple[ModelV4ComponentReceipt, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for receipt in receipts:
        row = receipt.as_row()
        rows.append({"player": player, "position": position, **row})
    return rows


def _source_coverage_rows(
    player: str,
    position: str,
    receipts: tuple[ModelV4ComponentReceipt, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for receipt in receipts:
        rows.append(
            {
                "player": player,
                "position": position,
                "section": receipt.component,
                "source_status": receipt.source_status,
                "coverage_status": _coverage_status(receipt),
                "warning": receipt.warning,
                "unavailable_reason": receipt.unavailable_reason,
            }
        )
    return rows


def _warning_rows(
    player: str,
    position: str,
    receipts: tuple[ModelV4ComponentReceipt, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for receipt in receipts:
        for warning in [part for part in receipt.warning.split("|") if part]:
            rows.append(
                {
                    "player": player,
                    "position": position,
                    "component": receipt.component,
                    "warning": warning,
                    "severity": "review",
                    "detail": receipt.unavailable_reason
                    or "Review warning emitted by v4 preview component calculator.",
                }
            )
    return rows


def _dynasty_asset_value(
    receipts: tuple[ModelV4ComponentReceipt, ...],
    lifecycle: str,
    *,
    formula_config: dict[str, object] | None = None,
) -> dict[str, object]:
    scoring_receipts = tuple(
        receipt for receipt in receipts if receipt.component != "confidence"
    )
    if lifecycle != "established_veteran":
        return {
            "dynasty_asset_value": round(
                sum(receipt.contribution for receipt in scoring_receipts),
                3,
            ),
            "value_basis": "weighted_sum",
            "scored_component_weight": round(
                sum(receipt.weight for receipt in scoring_receipts),
                3,
            ),
            "missing_component_weight": 0.0,
            "missing_value_components": "",
        }

    applicable_receipts = tuple(
        receipt
        for receipt in scoring_receipts
        if receipt.source_status != "not_applicable"
    )
    scored_receipts = tuple(
        receipt
        for receipt in applicable_receipts
        if not receipt.unavailable_reason
    )
    missing_receipts = tuple(
        receipt
        for receipt in applicable_receipts
        if receipt.unavailable_reason
    )
    scored_weight = sum(receipt.weight for receipt in scored_receipts)
    missing_weight = sum(receipt.weight for receipt in missing_receipts)
    scored_contribution = sum(receipt.contribution for receipt in scored_receipts)
    missing_components = "|".join(receipt.component for receipt in missing_receipts)
    if not missing_receipts:
        return {
            "dynasty_asset_value": round(scored_contribution, 3),
            "value_basis": "complete_applicable_evidence_weighted_sum",
            "scored_component_weight": round(scored_weight, 3),
            "missing_component_weight": 0.0,
            "missing_value_components": "",
        }
    if scored_weight >= 50.0:
        adjusted_value = (scored_contribution / scored_weight) * 100.0
        adjusted_value -= _missing_evidence_uncertainty_penalty(
            missing_weight,
            formula_config,
        )
        return {
            "dynasty_asset_value": round(max(0.0, adjusted_value), 3),
            "value_basis": "evidence_adjusted_missing_not_zero",
            "scored_component_weight": round(scored_weight, 3),
            "missing_component_weight": round(missing_weight, 3),
            "missing_value_components": missing_components,
        }
    return {
        "dynasty_asset_value": round(scored_contribution, 3),
        "value_basis": "insufficient_evidence_not_rankable",
        "scored_component_weight": round(scored_weight, 3),
        "missing_component_weight": round(missing_weight, 3),
        "missing_value_components": missing_components,
    }


def _missing_evidence_uncertainty_penalty(
    missing_weight: float,
    formula_config: dict[str, object] | None,
) -> float:
    policy = (
        formula_config.get("missing_evidence_policy", {})
        if isinstance(formula_config, dict)
        else {}
    )
    rate = _float_value(policy.get("missing_component_uncertainty_penalty_rate"), 0.0)
    cap = _float_value(policy.get("max_missing_component_uncertainty_penalty"), 0.0)
    if rate <= 0 or cap <= 0:
        return 0.0
    return min(cap, missing_weight * rate)


def _coverage_status(receipt: ModelV4ComponentReceipt) -> str:
    if receipt.source_status == "not_applicable":
        return "not_applicable"
    if receipt.unavailable_reason:
        return "missing"
    return "covered"


def _latest_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    grouped: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = _player_key_from_values(
            row.get("truth_set_player_name") or row.get("player_name"),
            row.get("position"),
        )
        if key == ("", ""):
            continue
        existing = grouped.get(key)
        if existing is None or _season(row) >= _season(existing):
            grouped[key] = row
    return grouped


def _by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    output: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = _player_key_from_values(
            row.get("player_name") or row.get("truth_set_player_name"),
            row.get("position"),
        )
        if key != ("", ""):
            output[key] = row
    return output


def _build_first_down_estimator_result(
    *,
    projection_path: Path,
    historical_stats_path: Path,
) -> FirstDownEstimatorResult | None:
    if not projection_path.exists() or not historical_stats_path.exists():
        return None
    return build_first_down_estimator_preview(projection_path, historical_stats_path)


def _player_key(row: dict[str, str]) -> tuple[str, str]:
    return _player_key_from_values(row.get("player_name"), row.get("position"))


def _player_key_from_values(name: object, position: object) -> tuple[str, str]:
    return (_name_key(name), str(position or "").strip().upper())


def _name_key(value: object) -> str:
    normalized = str(value or "").lower()
    normalized = normalized.replace("'", "").replace(".", "")
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _season(row: dict[str, str]) -> int:
    try:
        return int(float(str(row.get("season") or "0")))
    except ValueError:
        return 0


def _copy_fields(row: dict[str, str], fields: tuple[str, ...]) -> dict[str, str]:
    return {field: row[field] for field in fields if row.get(field, "") != ""}


def _joined(values: object) -> str:
    parts: list[str] = []
    for value in values:
        parts.extend(part for part in str(value).split("|") if part)
    return "|".join(dict.fromkeys(parts))


def _add_review_gap(row: dict[str, object], warning: str) -> None:
    if warning:
        row["warnings"] = _joined((row.get("warnings", ""), warning))
    row["review_gap_count"] = _int_value(row.get("review_gap_count")) + 1


def _int_value(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def _float_value(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value or ""))
    except (TypeError, ValueError):
        return default


def _projection_has_raw_stats(row: dict[str, str]) -> bool:
    return any(
        row.get(field, "") != ""
        for field in (
            "projected_passing_yards",
            "projected_passing_tds",
            "projected_interceptions",
            "projected_rushing_attempts",
            "projected_rushing_yards",
            "projected_rushing_tds",
            "projected_targets",
            "projected_receptions",
            "projected_receiving_yards",
            "projected_receiving_tds",
        )
    )


def _read_optional(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return _read_dicts(path)


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _summary_rows(summary: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key, value in summary.items():
        rows.append(
            {
                "metric": key,
                "value": json.dumps(value, sort_keys=True)
                if isinstance(value, (dict, list, tuple))
                else value,
            }
        )
    return rows
