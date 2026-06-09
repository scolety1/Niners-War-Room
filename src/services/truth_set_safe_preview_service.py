from __future__ import annotations

import csv
import json
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.lve_stats_first_preview_service import create_stats_first_model_preview
from src.utils.scoring import clamp_score

SAFE_PREVIEW_COMPARISON_HEADER = (
    "player_name",
    "position",
    "current_overall_rank",
    "preview_overall_rank",
    "rank_delta",
    "current_model_value",
    "preview_model_value",
    "model_value_delta",
    "current_keeper_score",
    "preview_keeper_score",
    "keeper_delta",
    "current_trade_value",
    "preview_trade_value",
    "trade_delta",
    "current_confidence",
    "preview_confidence",
    "confidence_delta",
    "delta_reason",
    "source_fields_used",
    "source_fields_rejected",
    "review_flags",
)

SAFE_PREVIEW_SOURCE_LOG_HEADER = (
    "player_name",
    "source",
    "field_group",
    "source_status",
    "model_usage",
    "detail",
)

SAFE_PREVIEW_SUMMARY_HEADER = (
    "metric",
    "value",
)


@dataclass(frozen=True)
class TruthSetSafePreviewResult:
    preview_id: str
    preview_path: Path
    normalized_path: Path
    output_path: Path
    contribution_path: Path
    comparison_rows: tuple[dict[str, object], ...]
    source_log_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def create_truth_set_safe_model_preview(
    *,
    active_output_path: str | Path,
    active_normalized_path: str | Path,
    projection_preview_path: str | Path,
    young_bridge_preview_path: str | Path,
    injury_path: str | Path,
    market_path: str | Path,
    production_path: str | Path,
    output_root: str | Path,
    preview_id: str,
    computed_at: str,
) -> TruthSetSafePreviewResult:
    active_outputs = _read_rows(active_output_path)
    active_normalized = _read_rows(active_normalized_path)
    projections = _read_rows(projection_preview_path)
    bridges = _read_rows(young_bridge_preview_path)
    injuries = _read_rows(injury_path)
    markets = _read_rows(market_path)
    production = _read_rows(production_path)

    projection_scores = _projection_normalized_scores(projections)
    projection_by_name = {_name_key(row.get("player_name")): row for row in projections}
    bridge_by_name = {_name_key(row.get("player_name")): row for row in bridges}
    injury_by_name = {_name_key(row.get("player_name")): row for row in injuries}
    market_scores = _market_normalized_scores(markets)
    truth_names = {_name_key(row.get("player_name")) for row in projections}
    source_logs: list[dict[str, object]] = []
    changed_rows: list[dict[str, object]] = []

    preview_rows: list[dict[str, object]] = []
    for row in active_normalized:
        preview = dict(row)
        key = _name_key(row.get("player_name"))
        if key in truth_names:
            used: list[str] = []
            rejected: list[str] = []
            review_flags: list[str] = []
            _apply_projection_overlay(
                preview,
                projection_scores.get(key),
                projection_by_name.get(key),
                used,
                review_flags,
            )
            _apply_bridge_overlay(preview, bridge_by_name.get(key), used, review_flags)
            _apply_injury_context(preview, injury_by_name.get(key), used, review_flags)
            _apply_market_context(preview, market_scores.get(key), used, review_flags)
            rejected.extend(
                _rejected_field_groups(
                    row.get("player_name"),
                    row.get("position"),
                    production,
                )
            )
            preview["truth_set_source_fields_used"] = "|".join(dict.fromkeys(used))
            preview["truth_set_source_fields_rejected"] = "|".join(dict.fromkeys(rejected))
            preview["truth_set_review_flags"] = "|".join(dict.fromkeys(review_flags))
            source_logs.extend(
                _source_log_rows(row.get("player_name"), used, rejected, review_flags)
            )
            changed_rows.append(preview)
        preview_rows.append(preview)

    preview_root = Path(output_root)
    preview_root.mkdir(parents=True, exist_ok=True)
    preview_path = preview_root / preview_id
    normalized_input_path = preview_root / f"{preview_id}_normalized_input.csv"
    if preview_path.exists():
        shutil.rmtree(preview_path)
    _write_dicts(normalized_input_path, tuple(preview_rows[0].keys()), tuple(preview_rows))
    preview_result = create_stats_first_model_preview(
        normalized_input_path,
        preview_root,
        preview_id=preview_id,
        computed_at=computed_at,
    )
    if not preview_result.created:
        raise ValueError(preview_result.message)

    _write_dicts(
        preview_result.preview_path / "stats_first_normalized_features.csv",
        tuple(preview_rows[0].keys()),
        tuple(preview_rows),
    )
    try:
        normalized_input_path.unlink()
    except FileNotFoundError:
        pass

    preview_outputs = _read_rows(preview_result.output_path)
    comparison_rows = _comparison_rows(
        active_outputs,
        preview_outputs,
        changed_rows,
    )
    summary = {
        "preview_id": preview_id,
        "truth_set_players": len(truth_names),
        "normalized_rows": len(preview_rows),
        "truth_set_rows_overlayed": len(changed_rows),
        "projection_rows_applied": sum(
            "truth_set_projection_recompute" in str(row.get("projection_source_status") or "")
            for row in changed_rows
        ),
        "young_bridge_rows_applied": sum(
            str(row.get("young_nfl_bridge_source") or "")
            == "truth_set_draft_capital_prior_preview"
            for row in changed_rows
        ),
        "market_context_rows_applied": sum(
            "truth_set_market_liquidity_context"
            in str(row.get("truth_set_source_fields_used") or "")
            for row in changed_rows
        ),
        "rejected_production_rows": sum(
            "production_stat_columns_rejected"
            in str(row.get("truth_set_source_fields_rejected") or "")
            for row in changed_rows
        ),
        "large_value_change_rows": sum(
            abs(_float(row.get("model_value_delta"), 0.0)) >= 8.0
            for row in comparison_rows
        ),
        "review_status": "review_only",
        "active_outputs_overwritten": False,
    }
    manifest_path = preview_result.preview_path / "truth_set_safe_preview_manifest.json"
    manifest_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return TruthSetSafePreviewResult(
        preview_id=preview_id,
        preview_path=preview_result.preview_path,
        normalized_path=preview_result.preview_path / "stats_first_normalized_features.csv",
        output_path=preview_result.output_path,
        contribution_path=preview_result.contribution_path,
        comparison_rows=tuple(comparison_rows),
        source_log_rows=tuple(source_logs),
        summary=summary,
    )


def write_safe_preview_comparison(path: str | Path, rows: tuple[dict[str, object], ...]) -> None:
    _write_dicts(path, SAFE_PREVIEW_COMPARISON_HEADER, rows)


def write_safe_preview_source_log(path: str | Path, rows: tuple[dict[str, object], ...]) -> None:
    _write_dicts(path, SAFE_PREVIEW_SOURCE_LOG_HEADER, rows)


def write_safe_preview_summary(path: str | Path, summary: dict[str, object]) -> None:
    rows = tuple({"metric": key, "value": value} for key, value in summary.items())
    _write_dicts(path, SAFE_PREVIEW_SUMMARY_HEADER, rows)


def _apply_projection_overlay(
    row: dict[str, object],
    projection_score: float | None,
    projection_row: dict[str, str] | None,
    used: list[str],
    review_flags: list[str],
) -> None:
    if projection_score is None:
        review_flags.append("missing_truth_set_projection")
        if projection_row:
            _append_projection_quality_review_flags(projection_row, review_flags)
        return
    row["lve_projection_value"] = projection_score
    row["projection_source_status"] = "truth_set_projection_recompute"
    if projection_row:
        row["projection_source_quality_status"] = projection_row.get(
            "projection_source_quality_status",
            "",
        )
        row["projection_source_quality_flags"] = projection_row.get(
            "projection_source_quality_flags",
            "",
        )
        _append_projection_quality_review_flags(projection_row, review_flags)
    row["warnings"] = _replace_warning(
        row.get("warnings"),
        remove={"local_baseline_projection_not_independent", "missing_projection_features"},
        add=_projection_warning_set(projection_row),
    )
    used.append("recomputed_projection_lve_points")


def _append_projection_quality_review_flags(
    projection_row: dict[str, str],
    review_flags: list[str],
) -> None:
    quality_flags = str(projection_row.get("projection_source_quality_flags") or "")
    for flag in quality_flags.split("|"):
        if flag:
            review_flags.append(f"projection_quality_{flag}")


def _projection_warning_set(projection_row: dict[str, str] | None) -> set[str]:
    warnings = {"truth_set_projection_recompute_preview"}
    quality_flags = str((projection_row or {}).get("projection_source_quality_flags") or "")
    if "missing_first_down_projection" in quality_flags:
        warnings.add("projection_first_downs_missing")
    if "team_mismatch" in quality_flags:
        warnings.add("projection_team_mismatch_review")
    if "missing_projection" in quality_flags:
        warnings.add("projection_missing_review")
    if "high_active_value_missing_projection" in quality_flags:
        warnings.add("high_active_value_missing_projection_review")
    return warnings


def _apply_bridge_overlay(
    row: dict[str, object],
    bridge: dict[str, str] | None,
    used: list[str],
    review_flags: list[str],
) -> None:
    if not bridge:
        return
    lifecycle = str(bridge.get("asset_lifecycle") or "")
    if lifecycle == "not_applicable_established_veteran":
        review_flags.append("established_veteran_draft_capital_not_scored")
        return
    if bridge.get("draft_capital_source_status") == "missing_source_row":
        review_flags.append("missing_young_bridge_source_row")
        return
    if _float(bridge.get("draft_capital_prior_score")) is None:
        review_flags.append("missing_draft_capital_prior")
        return
    row["draft_year"] = bridge.get("draft_year", "")
    row["draft_round"] = (
        ""
        if str(bridge.get("nfl_draft_round") or "").upper() == "UDFA"
        else bridge.get("nfl_draft_round", "")
    )
    row["draft_overall"] = bridge.get("nfl_draft_pick", "")
    row["young_nfl_bridge_source"] = "truth_set_draft_capital_prior_preview"
    row["warnings"] = _append_warning(row.get("warnings"), "truth_set_young_bridge_prior_preview")
    used.append("young_bridge_draft_capital_prior")
    if bridge.get("college_production_context"):
        used.append("young_college_context_display_only")
    if bridge.get("athletic_testing_context"):
        used.append("young_athletic_context_display_only")
    if bridge.get("warning_flags"):
        review_flags.extend(str(bridge.get("warning_flags")).split("|"))


def _apply_injury_context(
    row: dict[str, object],
    injury: dict[str, str] | None,
    used: list[str],
    review_flags: list[str],
) -> None:
    if not injury:
        return
    if injury.get("source_url") and (
        injury.get("current_injury") or injury.get("body_part") or injury.get("ir_pup_status")
    ):
        row["warnings"] = _append_warning(row.get("warnings"), "truth_set_sourced_injury_context")
        used.append("truth_set_sourced_injury_context")
    else:
        review_flags.append("injury_context_unsourced_or_healthy_not_scored")


def _apply_market_context(
    row: dict[str, object],
    market_score: float | None,
    used: list[str],
    review_flags: list[str],
) -> None:
    if market_score is None:
        review_flags.append("missing_truth_set_market_liquidity")
        return
    row["market_liquidity"] = market_score
    used.append("truth_set_market_liquidity_context")


def _comparison_rows(
    active_outputs: list[dict[str, str]],
    preview_outputs: list[dict[str, str]],
    changed_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    active_by_name = {_name_key(row.get("player_name")): row for row in active_outputs}
    preview_by_name = {_name_key(row.get("player_name")): row for row in preview_outputs}
    changed_by_name = {_name_key(row.get("player_name")): row for row in changed_rows}
    rows: list[dict[str, object]] = []
    for key, changed in changed_by_name.items():
        active = active_by_name.get(key, {})
        preview = preview_by_name.get(key, {})
        current_value = _float(active.get("private_lve_value"), 0.0)
        preview_value = _float(preview.get("private_lve_value"), 0.0)
        rows.append(
            {
                "player_name": changed.get("player_name", active.get("player_name", "")),
                "position": changed.get("position", active.get("position", "")),
                "current_overall_rank": active.get("overall_rank", ""),
                "preview_overall_rank": preview.get("overall_rank", ""),
                "rank_delta": _rank_delta(active.get("overall_rank"), preview.get("overall_rank")),
                "current_model_value": round(current_value, 2),
                "preview_model_value": round(preview_value, 2),
                "model_value_delta": round(preview_value - current_value, 2),
                "current_keeper_score": active.get("keeper_score", ""),
                "preview_keeper_score": preview.get("keeper_score", ""),
                "keeper_delta": round(
                    _float(preview.get("keeper_score"), 0.0)
                    - _float(active.get("keeper_score"), 0.0),
                    2,
                ),
                "current_trade_value": active.get("trade_value", ""),
                "preview_trade_value": preview.get("trade_value", ""),
                "trade_delta": round(
                    _float(preview.get("trade_value"), 0.0)
                    - _float(active.get("trade_value"), 0.0),
                    2,
                ),
                "current_confidence": active.get("confidence_score", ""),
                "preview_confidence": preview.get("confidence_score", ""),
                "confidence_delta": round(
                    _float(preview.get("confidence_score"), 0.0)
                    - _float(active.get("confidence_score"), 0.0),
                    2,
                ),
                "delta_reason": _delta_reason(changed),
                "source_fields_used": changed.get("truth_set_source_fields_used", ""),
                "source_fields_rejected": changed.get("truth_set_source_fields_rejected", ""),
                "review_flags": changed.get("truth_set_review_flags", ""),
            }
        )
    return sorted(rows, key=lambda row: abs(_float(row["model_value_delta"], 0.0)), reverse=True)


def _source_log_rows(
    player_name: object,
    used: list[str],
    rejected: list[str],
    review_flags: list[str],
) -> list[dict[str, object]]:
    player = str(player_name or "")
    rows: list[dict[str, object]] = []
    for source in used:
        rows.append(
            {
                "player_name": player,
                "source": source,
                "field_group": source,
                "source_status": "safe_preview_applied",
                "model_usage": _usage_for_source(source),
                "detail": "Applied only in Truth Set safe preview.",
            }
        )
    for source in rejected:
        rows.append(
            {
                "player_name": player,
                "source": source,
                "field_group": source,
                "source_status": "rejected",
                "model_usage": "not_used",
                "detail": "Rejected by Truth Set Lab eligibility rules.",
            }
        )
    for flag in review_flags:
        rows.append(
            {
                "player_name": player,
                "source": flag,
                "field_group": flag,
                "source_status": "review_flag",
                "model_usage": "context_only",
                "detail": "Flag retained for review; no fake data invented.",
            }
        )
    return rows


def _projection_normalized_scores(rows: list[dict[str, str]]) -> dict[str, float]:
    by_position: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        if row.get("projection_availability_status") != "projection_stat_line_present":
            continue
        points = _float(row.get("recomputed_lve_points"))
        if points is None:
            continue
        by_position[str(row.get("position") or "")].append(
            (_name_key(row.get("player_name")), points)
        )
    normalized: dict[str, float] = {}
    for entries in by_position.values():
        values = [value for _, value in entries]
        low = min(values)
        high = max(values)
        for key, value in entries:
            if high == low:
                normalized[key] = 50.0
            else:
                normalized[key] = round(
                    clamp_score(35.0 + (60.0 * ((value - low) / (high - low)))),
                    2,
                )
    return normalized


def _market_normalized_scores(rows: list[dict[str, str]]) -> dict[str, float]:
    values = [
        (_name_key(row.get("player_name")), _float(row.get("trade_value_number")))
        for row in rows
        if _float(row.get("trade_value_number")) is not None
    ]
    if not values:
        return {}
    raw_values = [value for _, value in values if value is not None]
    low = min(raw_values)
    high = max(raw_values)
    output: dict[str, float] = {}
    for key, value in values:
        if value is None:
            continue
        output[key] = (
            50.0
            if high == low
            else round(35.0 + (60.0 * ((value - low) / (high - low))), 2)
        )
    return output


def _rejected_field_groups(
    player_name: object,
    position: object,
    production_rows: list[dict[str, str]],
) -> list[str]:
    rejected = [
        "production_stat_columns_rejected",
        "supplied_projection_points_rejected",
    ]
    if str(position or "").upper() == "RB":
        rejected.append("unsafe_rb_role_text_rejected")
    if _name_key(player_name) not in {_name_key(row.get("player_name")) for row in production_rows}:
        rejected.append("production_row_missing_or_unmatched")
    return rejected


def _delta_reason(row: dict[str, object]) -> str:
    used = str(row.get("truth_set_source_fields_used") or "")
    reasons = []
    if "recomputed_projection_lve_points" in used:
        reasons.append("projection recompute")
    if "young_bridge_draft_capital_prior" in used:
        reasons.append("young bridge prior")
    if "truth_set_market_liquidity_context" in used:
        reasons.append("market context")
    if "truth_set_sourced_injury_context" in used:
        reasons.append("injury context")
    return "; ".join(reasons) if reasons else "no safe scoring fields applied"


def _usage_for_source(source: str) -> str:
    if source == "truth_set_market_liquidity_context":
        return "trade_context_only"
    if "injury" in source:
        return "confidence_context_only"
    if "college_context" in source or "athletic_context" in source:
        return "display_context_only"
    return "model_preview_only"


def _replace_warning(value: object, *, remove: set[str], add: set[str]) -> str:
    parts = {part for part in str(value or "").split("|") if part and part not in remove}
    parts.update(add)
    return "|".join(sorted(parts))


def _append_warning(value: object, warning: str) -> str:
    parts = {part for part in str(value or "").split("|") if part}
    parts.add(warning)
    return "|".join(sorted(parts))


def _rank_delta(current: object, preview: object) -> object:
    current_rank = _float(current)
    preview_rank = _float(preview)
    if current_rank is None or preview_rank is None:
        return ""
    return int(current_rank - preview_rank)


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _name_key(value: object) -> str:
    text = str(value or "").lower().replace("’", "'")
    text = text.replace("iii", "")
    return re.sub(r"[^a-z0-9]+", "", text)


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    path: str | Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
