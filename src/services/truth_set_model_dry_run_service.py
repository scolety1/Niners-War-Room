from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.lve_stats_first_veteran_formula_service import score_stats_first_veteran_row
from src.utils.scoring import clamp_score

TRUTH_SET_MODEL_DRY_RUN_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "current_active_model_value",
    "truth_set_preview_model_value",
    "delta",
    "delta_reason",
    "current_confidence",
    "truth_set_preview_confidence",
    "confidence_impact",
    "source_fields_used",
    "source_fields_rejected",
    "large_change_flag",
    "review_flags",
)

TRUTH_SET_MODEL_DRY_RUN_REJECTION_HEADER = (
    "player_name",
    "source",
    "field_group",
    "rejection_reason",
)

TRUTH_SET_MODEL_DRY_RUN_SUMMARY_HEADER = (
    "metric",
    "value",
)


@dataclass(frozen=True)
class TruthSetModelDryRunResult:
    rows: tuple[dict[str, object], ...]
    rejected_rows: tuple[dict[str, str], ...]
    summary: dict[str, object]


def build_truth_set_model_dry_run(
    *,
    active_output_path: str | Path,
    normalized_features_path: str | Path,
    projection_preview_path: str | Path,
    young_bridge_preview_path: str | Path,
    production_clean_path: str | Path,
    injury_path: str | Path,
    trade_liquidity_path: str | Path,
) -> TruthSetModelDryRunResult:
    active_rows = _read_rows(active_output_path)
    feature_rows = _read_rows(normalized_features_path)
    projection_rows = _read_rows(projection_preview_path)
    bridge_rows = _read_rows(young_bridge_preview_path)
    production_rows = _read_rows(production_clean_path)
    injury_rows = _read_rows(injury_path)
    market_rows = _read_rows(trade_liquidity_path)

    active_by_name = {_name_key(row.get("player_name")): row for row in active_rows}
    features_by_name = {_name_key(row.get("player_name")): row for row in feature_rows}
    bridge_by_name = {_name_key(row.get("player_name")): row for row in bridge_rows}
    injury_by_name = {_name_key(row.get("player_name")): row for row in injury_rows}
    market_by_name = {_name_key(row.get("player_name")): row for row in market_rows}
    projection_scores = _projection_normalized_scores(projection_rows)
    truth_players = _ordered_truth_players(projection_rows)

    rows: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    for projection in truth_players:
        player = str(projection.get("player_name") or "")
        key = _name_key(player)
        active = active_by_name.get(key, {})
        feature = features_by_name.get(key, {})
        if not feature:
            rows.append(_missing_active_row(player, projection, active))
            rejected.extend(_rejected_rows_for_player(player, production_rows))
            continue

        preview_feature = dict(feature)
        source_used: list[str] = []
        review_flags: list[str] = []
        rejected_fields = [
            "production_stat_columns_rejected",
            "supplied_projection_points_rejected",
            "market_excluded_from_private_value",
            "injury_excluded_from_private_value",
        ]

        projection_norm = projection_scores.get(key)
        if projection_norm is not None:
            preview_feature["lve_projection_value"] = projection_norm
            preview_feature["projection_source_status"] = "truth_set_recomputed_projection"
            preview_feature["warnings"] = _replace_warning(
                preview_feature.get("warnings"),
                remove={
                    "local_baseline_projection_not_independent",
                    "missing_projection_features",
                },
                add={"truth_set_projection_recompute_preview"},
            )
            source_used.append("recomputed_projection_lve_points")
            if projection.get("first_down_projection_status") == "estimated_missing":
                review_flags.append("projection_first_downs_missing")
        else:
            review_flags.append("missing_truth_set_projection")

        bridge = bridge_by_name.get(key)
        if bridge:
            _apply_bridge_preview(preview_feature, bridge, source_used, review_flags)
            if _has_context(bridge, "college_production_context"):
                source_used.append("young_college_context_display_only")
                rejected_fields.append("young_college_context_not_scored")
            if _has_context(bridge, "athletic_testing_context"):
                source_used.append("young_athletic_context_display_only")
                rejected_fields.append("young_athletic_context_not_scored")
            if "subjective_note_language" in str(bridge.get("warning_flags") or ""):
                rejected_fields.append("subjective_young_notes_not_scored")

        if _has_populated_market(market_by_name.get(key)):
            source_used.append("trade_liquidity_context_only")
        if _has_injury_context(injury_by_name.get(key)):
            source_used.append("injury_context_only")

        current_value = _float(
            active.get("private_lve_value") or active.get("private_score"),
            _float(feature.get("private_stat_value"), 0.0),
        )
        current_confidence = _float(
            active.get("confidence_score") or feature.get("confidence"),
            0.0,
        )
        score = score_stats_first_veteran_row(preview_feature)
        preview_value = score.private_lve_value
        delta = round(preview_value - current_value, 2)
        confidence_delta = round(score.confidence_score - current_confidence, 2)
        if abs(delta) >= 8:
            review_flags.append("large_preview_model_value_change")

        rows.append(
            {
                "player_name": player,
                "position": projection.get("position", feature.get("position", "")),
                "nfl_team": projection.get("nfl_team", feature.get("team", "")),
                "current_active_model_value": round(current_value, 2),
                "truth_set_preview_model_value": preview_value,
                "delta": delta,
                "delta_reason": _delta_reason(delta, source_used, review_flags),
                "current_confidence": round(current_confidence, 2),
                "truth_set_preview_confidence": score.confidence_score,
                "confidence_impact": _confidence_impact(confidence_delta, source_used),
                "source_fields_used": "|".join(dict.fromkeys(source_used)),
                "source_fields_rejected": "|".join(dict.fromkeys(rejected_fields)),
                "large_change_flag": "yes" if abs(delta) >= 8 else "no",
                "review_flags": "|".join(dict.fromkeys(review_flags)),
            }
        )
        rejected.extend(_rejected_rows_for_player(player, production_rows))

    summary = {
        "rows": len(rows),
        "players_with_active_model_row": sum(
            1 for row in rows if row["truth_set_preview_model_value"] != ""
        ),
        "large_change_rows": sum(1 for row in rows if row["large_change_flag"] == "yes"),
        "projection_recompute_rows_used": sum(
            1 for row in rows if "recomputed_projection_lve_points" in row["source_fields_used"]
        ),
        "young_bridge_rows_used": sum(
            1 for row in rows if "young_bridge_draft_capital_prior" in row["source_fields_used"]
        ),
        "production_fields_rejected": len(rejected),
        "scoring_effect": "preview-only dry run; active model outputs not overwritten",
    }
    return TruthSetModelDryRunResult(
        rows=tuple(rows),
        rejected_rows=tuple(rejected),
        summary=summary,
    )


def write_truth_set_model_dry_run(path: str | Path, rows: tuple[dict[str, object], ...]) -> None:
    _write_dicts(path, TRUTH_SET_MODEL_DRY_RUN_HEADER, rows)


def write_truth_set_model_dry_run_rejections(
    path: str | Path,
    rows: tuple[dict[str, str], ...],
) -> None:
    _write_dicts(path, TRUTH_SET_MODEL_DRY_RUN_REJECTION_HEADER, rows)


def write_truth_set_model_dry_run_summary(path: str | Path, summary: dict[str, object]) -> None:
    rows = tuple({"metric": key, "value": value} for key, value in summary.items())
    _write_dicts(path, TRUTH_SET_MODEL_DRY_RUN_SUMMARY_HEADER, rows)


def write_truth_set_model_dry_run_summary_json(
    path: str | Path,
    summary: dict[str, object],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


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


def _ordered_truth_players(projection_rows: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    return tuple(projection_rows)


def _apply_bridge_preview(
    preview_feature: dict[str, object],
    bridge: dict[str, str],
    source_used: list[str],
    review_flags: list[str],
) -> None:
    lifecycle = str(bridge.get("asset_lifecycle") or "")
    if lifecycle == "not_applicable_established_veteran":
        review_flags.append("established_veteran_draft_capital_not_scored")
        return
    if bridge.get("draft_capital_source_status") == "missing_source_row":
        review_flags.append("missing_young_bridge_source_row")
        return
    prior = _float(bridge.get("draft_capital_prior_score"))
    if prior is None:
        review_flags.append("missing_draft_capital_prior")
        return

    preview_feature["draft_year"] = bridge.get("draft_year", "")
    preview_feature["draft_round"] = _draft_round_value(bridge.get("nfl_draft_round"))
    preview_feature["draft_overall"] = bridge.get("nfl_draft_pick", "")
    preview_feature["young_nfl_bridge_source"] = "truth_set_draft_capital_prior_preview"
    source_used.append("young_bridge_draft_capital_prior")


def _draft_round_value(value: object) -> object:
    text = str(value or "").strip()
    if text.upper() == "UDFA":
        return ""
    return text


def _missing_active_row(
    player: str,
    projection: dict[str, str],
    active: dict[str, str],
) -> dict[str, object]:
    return {
        "player_name": player,
        "position": projection.get("position", ""),
        "nfl_team": projection.get("nfl_team", ""),
        "current_active_model_value": active.get("private_lve_value", ""),
        "truth_set_preview_model_value": "",
        "delta": "",
        "delta_reason": "missing active normalized feature row; no dry-run score",
        "current_confidence": active.get("confidence_score", ""),
        "truth_set_preview_confidence": "",
        "confidence_impact": "not evaluated",
        "source_fields_used": "",
        "source_fields_rejected": "production_stat_columns_rejected",
        "large_change_flag": "no",
        "review_flags": "missing_active_normalized_feature_row",
    }


def _rejected_rows_for_player(
    player: str,
    production_rows: list[dict[str, str]],
) -> tuple[dict[str, str], ...]:
    if _name_key(player) not in {_name_key(row.get("player_name")) for row in production_rows}:
        return ()
    return (
        {
            "player_name": player,
            "source": "production",
            "field_group": "all parsed production stat columns",
            "rejection_reason": (
                "Production intake field alignment is untrusted; rejected until re-exported."
            ),
        },
        {
            "player_name": player,
            "source": "projections",
            "field_group": "supplied projected_lve_points_if_calculable",
            "rejection_reason": (
                "Supplied projection points are non-LVE; recomputed points used instead."
            ),
        },
    )


def _delta_reason(delta: float, source_used: list[str], review_flags: list[str]) -> str:
    if not source_used:
        return "No safe truth-set scoring fields applied."
    pieces = []
    if "recomputed_projection_lve_points" in source_used:
        pieces.append("projection recompute")
    if "young_bridge_draft_capital_prior" in source_used:
        pieces.append("young bridge prior")
    if abs(delta) >= 8:
        pieces.append("large change needs review")
    if "missing_truth_set_projection" in review_flags:
        pieces.append("projection missing")
    return "; ".join(pieces) if pieces else "Context-only fields used."


def _confidence_impact(delta: float, source_used: list[str]) -> str:
    if "recomputed_projection_lve_points" not in source_used:
        return "No confidence lift from missing projection evidence."
    if delta > 0:
        return f"Preview confidence +{delta:.2f}; first-down projections still missing."
    if delta < 0:
        return f"Preview confidence {delta:.2f}; first-down projections still missing."
    return "Preview confidence unchanged; first-down projections still missing."


def _replace_warning(
    value: object,
    *,
    remove: set[str],
    add: set[str],
) -> str:
    parts = {part for part in str(value or "").split("|") if part and part not in remove}
    parts.update(add)
    return "|".join(sorted(parts))


def _has_context(row: dict[str, str] | None, field: str) -> bool:
    return bool(row and str(row.get(field) or "").strip())


def _has_populated_market(row: dict[str, str] | None) -> bool:
    return bool(row and _float(row.get("trade_value_number")) is not None)


def _has_injury_context(row: dict[str, str] | None) -> bool:
    if not row:
        return False
    return any(
        str(row.get(field) or "").strip()
        for field in (
            "current_injury",
            "body_part",
            "ir_pup_status",
            "2025_games_missed",
            "2024_games_missed",
            "notes",
        )
    )


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _name_key(value: object) -> str:
    text = str(value or "").lower()
    text = text.replace("’", "'").replace("`", "'")
    text = text.replace("iii", "")
    text = text.replace("jr.", "jr").replace("jr", "jr")
    return re.sub(r"[^a-z0-9]+", "", text)


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    path: str | Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
