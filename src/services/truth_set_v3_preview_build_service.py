from __future__ import annotations

import csv
import json
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.lve_stats_first_preview_service import create_stats_first_model_preview
from src.utils.scoring import clamp_score

V3_SOURCE_COVERAGE_HEADER = (
    "player_name",
    "position",
    "bucket",
    "source_status",
    "model_usage",
    "coverage_status",
    "fields",
    "notes",
)

V3_REJECTED_FIELD_LOG_HEADER = (
    "player_name",
    "position",
    "field_group",
    "rejection_reason",
    "source",
    "model_usage",
)

V3_MOVEMENT_HEADER = (
    "player_name",
    "position",
    "v2_overall_rank",
    "v3_overall_rank",
    "rank_delta",
    "v2_model_value",
    "v3_model_value",
    "model_value_delta",
    "movement_reason",
    "review_flags",
)

V3_SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class TruthSetV3PreviewBuildResult:
    preview_id: str
    preview_path: Path
    normalized_path: Path
    output_path: Path
    contribution_path: Path
    source_coverage_path: Path
    rejected_field_log_path: Path
    movement_path: Path
    summary_path: Path
    summary: dict[str, object]


def build_truth_set_v3_model_preview(
    *,
    active_output_path: str | Path,
    active_normalized_path: str | Path,
    v2_output_path: str | Path,
    production_season_path: str | Path,
    usage_season_path: str | Path,
    snap_share_season_path: str | Path,
    projection_recompute_path: str | Path,
    young_bridge_path: str | Path,
    injury_path: str | Path,
    market_path: str | Path,
    route_honesty_path: str | Path,
    output_root: str | Path,
    preview_id: str,
    computed_at: str,
) -> TruthSetV3PreviewBuildResult:
    active_normalized = _read_rows(active_normalized_path)
    v2_outputs = _read_rows(v2_output_path) if Path(v2_output_path).exists() else []
    production_rows = _read_rows(production_season_path)
    usage_rows = _read_rows(usage_season_path)
    snap_rows = _read_rows(snap_share_season_path)
    projection_rows = _read_rows(projection_recompute_path)
    young_bridge_rows = _read_rows(young_bridge_path)
    injury_rows = _read_rows(injury_path)
    market_rows = _read_rows(market_path)
    route_rows = _read_rows(route_honesty_path)

    production_by_name = _latest_weighted_by_name(production_rows, "truth_set_player_name")
    usage_by_name = _latest_weighted_by_name(usage_rows, "truth_set_player_name")
    snap_by_name = _latest_weighted_by_name(snap_rows, "truth_set_player_name")
    projections_by_name = {_name_key(row.get("player_name")): row for row in projection_rows}
    bridge_by_name = {_name_key(row.get("player_name")): row for row in young_bridge_rows}
    injury_by_name = {_name_key(row.get("player_name")): row for row in injury_rows}
    market_by_name = {_name_key(row.get("player_name")): row for row in market_rows}
    route_status = _route_status_from_field_contract(route_rows)
    truth_names = (
        set(production_by_name)
        | set(usage_by_name)
        | set(snap_by_name)
        | set(projections_by_name)
        | set(bridge_by_name)
    )

    source_coverage: list[dict[str, object]] = []
    rejected_fields: list[dict[str, object]] = []
    changed_rows: list[dict[str, object]] = []
    preview_rows: list[dict[str, object]] = []

    production_scores = _production_scores(production_by_name)
    first_down_scores = _first_down_scores(production_by_name)
    efficiency_scores = _efficiency_scores(production_by_name)
    projection_scores = _projection_scores(projection_rows)
    usage_scores = _usage_scores(usage_by_name, snap_by_name)
    market_scores = _market_scores(market_rows)

    for row in active_normalized:
        preview = dict(row)
        key = _name_key(row.get("player_name"))
        if key in truth_names:
            player_name = str(row.get("player_name") or "")
            position = str(row.get("position") or "")
            used: list[str] = []
            review_flags: list[str] = []

            _apply_production(
                preview,
                production_by_name.get(key),
                production_scores.get(key),
                first_down_scores.get(key),
                efficiency_scores.get(key),
                used,
                review_flags,
                source_coverage,
            )
            _apply_usage(
                preview,
                usage_by_name.get(key),
                snap_by_name.get(key),
                usage_scores.get(key, {}),
                used,
                review_flags,
                source_coverage,
            )
            _apply_projection(
                preview,
                projections_by_name.get(key),
                projection_scores.get(key),
                used,
                review_flags,
                source_coverage,
            )
            _apply_young_bridge(
                preview,
                bridge_by_name.get(key),
                used,
                review_flags,
                source_coverage,
            )
            _apply_injury_context(
                preview,
                injury_by_name.get(key),
                used,
                review_flags,
                source_coverage,
            )
            _apply_market_context(
                preview,
                market_by_name.get(key),
                market_scores.get(key),
                used,
                review_flags,
                source_coverage,
            )
            _apply_route_honesty(
                preview,
                route_status,
                used,
                review_flags,
                source_coverage,
            )
            rejected_fields.extend(_rejected_rows(player_name, position))
            preview["truth_set_v3_source_fields_used"] = "|".join(dict.fromkeys(used))
            preview["truth_set_v3_review_flags"] = "|".join(dict.fromkeys(review_flags))
            preview["source_version"] = "truth_set_lab_v3_preview_free_structured_data"
            preview["computed_at"] = computed_at
            changed_rows.append(preview)
        preview_rows.append(preview)

    preview_root = Path(output_root)
    preview_root.mkdir(parents=True, exist_ok=True)
    preview_path = preview_root / preview_id
    normalized_input_path = preview_root / f"{preview_id}_normalized_input.csv"
    if preview_path.exists():
        shutil.rmtree(preview_path)
    _write_dicts(normalized_input_path, tuple(preview_rows[0].keys()), preview_rows)
    stats_result = create_stats_first_model_preview(
        normalized_input_path,
        preview_root,
        preview_id=preview_id,
        computed_at=computed_at,
    )
    if not stats_result.created:
        raise ValueError(stats_result.message)
    normalized_path = stats_result.preview_path / "stats_first_normalized_features.csv"
    _write_dicts(normalized_path, tuple(preview_rows[0].keys()), preview_rows)
    try:
        normalized_input_path.unlink()
    except FileNotFoundError:
        pass

    v3_outputs = _read_rows(stats_result.output_path)
    movement_rows = _movement_rows(v2_outputs, v3_outputs, changed_rows)
    summary = {
        "preview_id": preview_id,
        "review_status": "review_only",
        "active_outputs_overwritten": False,
        "truth_set_players": len(truth_names),
        "normalized_rows": len(preview_rows),
        "truth_set_rows_overlayed": len(changed_rows),
        "production_rows_applied": sum(
            "v3_native_production" in _used(row) for row in changed_rows
        ),
        "usage_rows_applied": sum("v3_derived_usage" in _used(row) for row in changed_rows),
        "snap_share_rows_applied": sum("v3_snap_share" in _used(row) for row in changed_rows),
        "projection_rows_applied": sum(
            "v3_projection_recompute" in _used(row) for row in changed_rows
        ),
        "young_bridge_rows_applied": sum(
            "v3_young_bridge_prior" in _used(row) for row in changed_rows
        ),
        "sourced_injury_context_rows": sum(
            "v3_sourced_injury_context" in _used(row) for row in changed_rows
        ),
        "sourced_market_context_rows": sum(
            "v3_market_context_only" in _used(row) for row in changed_rows
        ),
        "route_rows_quarantined": sum(
            "v3_route_values_quarantined" in _used(row) for row in changed_rows
        ),
        "rejected_field_rows": len(rejected_fields),
        "large_v2_movement_rows": sum(
            abs(_float(row.get("model_value_delta"), 0.0) or 0.0) >= 8.0 for row in movement_rows
        ),
    }
    source_coverage_path = stats_result.preview_path / "truth_set_v3_source_coverage.csv"
    rejected_field_log_path = stats_result.preview_path / "truth_set_v3_rejected_field_log.csv"
    movement_path = stats_result.preview_path / "truth_set_v3_movement_vs_v2.csv"
    summary_path = stats_result.preview_path / "truth_set_v3_preview_summary.csv"
    _write_dicts(source_coverage_path, V3_SOURCE_COVERAGE_HEADER, source_coverage)
    _write_dicts(rejected_field_log_path, V3_REJECTED_FIELD_LOG_HEADER, rejected_fields)
    _write_dicts(movement_path, V3_MOVEMENT_HEADER, movement_rows)
    _write_dicts(summary_path, V3_SUMMARY_HEADER, _summary_rows(summary))
    (stats_result.preview_path / "truth_set_v3_preview_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (stats_result.preview_path / "truth_set_v3_preview_manifest.json").write_text(
        json.dumps(
            {
                **summary,
                "active_output_path": str(active_output_path),
                "active_normalized_path": str(active_normalized_path),
                "v2_output_path": str(v2_output_path),
                "apply_boundary": (
                    "preview_only; active rankings and data packs were not overwritten"
                ),
                "excluded_sources": (
                    "rejected production CSV; rejected role/usage CSV; supplied non-LVE "
                    "projection points; fake route values"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return TruthSetV3PreviewBuildResult(
        preview_id=preview_id,
        preview_path=stats_result.preview_path,
        normalized_path=normalized_path,
        output_path=stats_result.output_path,
        contribution_path=stats_result.contribution_path,
        source_coverage_path=source_coverage_path,
        rejected_field_log_path=rejected_field_log_path,
        movement_path=movement_path,
        summary_path=summary_path,
        summary=summary,
    )


def _apply_production(
    row: dict[str, object],
    production: dict[str, object] | None,
    production_score: float | None,
    first_down_score: float | None,
    efficiency_score: float | None,
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    if not production:
        review_flags.append("v3_missing_native_production")
        coverage.append(
            _coverage(
                player,
                position,
                "production",
                "missing",
                "not_used",
                "missing",
                "",
                "No native nflverse production row matched.",
            )
        )
        return
    row["weighted_recent_lve_ppg_score"] = _round(production_score, 50.0)
    row["expected_lve_points_score"] = _round(production_score, 50.0)
    row["first_down_td_fit"] = _round(first_down_score, 50.0)
    row["efficiency_score"] = _round(efficiency_score, 50.0)
    row["warnings"] = _replace_warnings(
        row.get("warnings"),
        remove={"missing_lve_scoring_history", "stale_lve_scoring_source"},
        add={"v3_native_nflverse_production_preview"},
    )
    used.append("v3_native_production")
    coverage.append(
        _coverage(
            player,
            position,
            "production",
            "imported_real_data",
            "model_preview_only",
            "covered",
            "weighted_recent_lve_ppg_score|expected_lve_points_score|efficiency_score|first_down_td_fit",
            "Native nflverse player stats with real rushing/receiving first downs.",
        )
    )


def _apply_usage(
    row: dict[str, object],
    usage: dict[str, object] | None,
    snap: dict[str, object] | None,
    usage_scores: dict[str, float],
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    if usage:
        row["workload_earning"] = _round(usage_scores.get("workload_earning"), 50.0)
        row["target_earning_stability"] = _round(
            usage_scores.get("target_earning_stability"),
            50.0,
        )
        used.append("v3_derived_usage")
        coverage.append(
            _coverage(
                player,
                position,
                "role_usage",
                "derived_real_data",
                "model_preview_only",
                "covered",
                "target_share|rb_carry_share|rb_target_share|weighted_opportunities|red_zone|goal_line",
                "Derived from nflverse play-by-play. No route metrics estimated.",
            )
        )
    else:
        review_flags.append("v3_missing_pbp_usage")
        coverage.append(
            _coverage(
                player,
                position,
                "role_usage",
                "missing",
                "not_used",
                "missing",
                "",
                "No play-by-play usage row matched.",
            )
        )
    if snap:
        row["role_security"] = _round(usage_scores.get("role_security"), 50.0)
        row["warnings"] = _replace_warnings(
            row.get("warnings"),
            remove={"missing_participation_proxy", "missing_snap_counts"},
            add={"v3_snap_share_preview"},
        )
        used.append("v3_snap_share")
        coverage.append(
            _coverage(
                player,
                position,
                "snap_share",
                "imported_real_data",
                "model_preview_only",
                "covered",
                "offense_snaps|avg_snap_share",
                "Imported nflverse snap counts. This is snap share, not route participation.",
            )
        )
    else:
        review_flags.append("v3_missing_snap_share")
        coverage.append(
            _coverage(
                player,
                position,
                "snap_share",
                "missing",
                "not_used",
                "missing",
                "",
                "No snap-share row matched.",
            )
        )


def _apply_projection(
    row: dict[str, object],
    projection: dict[str, str] | None,
    projection_score: float | None,
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    if projection_score is None or not projection:
        review_flags.append("v3_missing_valid_projection_recompute")
        coverage.append(
            _coverage(
                player,
                position,
                "projection",
                "missing_projection",
                "not_used",
                "missing",
                "",
                "No valid recomputed projection stat line.",
            )
        )
        return
    row["lve_projection_value"] = _round(projection_score, 50.0)
    row["projection_source_status"] = "truth_set_v3_projection_recompute"
    quality_flags = str(projection.get("projection_source_quality_flags") or "")
    row["warnings"] = _replace_warnings(
        row.get("warnings"),
        remove={"local_baseline_projection_not_independent", "missing_projection_features"},
        add={"v3_projection_recompute_preview", *_projection_warning_set(quality_flags)},
    )
    if quality_flags:
        review_flags.extend(
            f"projection_quality_{flag}" for flag in quality_flags.split("|") if flag
        )
    used.append("v3_projection_recompute")
    coverage.append(
        _coverage(
            player,
            position,
            "projection",
            "derived_real_data",
            "model_preview_only",
            "covered",
            "recomputed_lve_points",
            "Raw projection stats recomputed into LVE scoring. Supplied non-LVE points rejected.",
        )
    )


def _apply_young_bridge(
    row: dict[str, object],
    bridge: dict[str, str] | None,
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    if not bridge:
        coverage.append(
            _coverage(
                player,
                position,
                "young_bridge_prior",
                "not_applicable",
                "not_used",
                "not_applicable",
                "",
                "No young bridge row matched.",
            )
        )
        return
    lifecycle = str(bridge.get("asset_lifecycle") or "")
    if lifecycle == "not_applicable_established_veteran":
        review_flags.append("established_veteran_draft_capital_not_scored")
        coverage.append(
            _coverage(
                player,
                position,
                "young_bridge_prior",
                "not_applicable_established_veteran",
                "display_context_only",
                "not_applicable",
                "",
                "Established veteran; draft capital not scored.",
            )
        )
        return
    score = _float(bridge.get("draft_capital_prior_score"))
    if score is None or bridge.get("draft_capital_source_status") == "missing_source_row":
        review_flags.append("v3_missing_young_bridge_prior")
        coverage.append(
            _coverage(
                player,
                position,
                "young_bridge_prior",
                "missing",
                "not_used",
                "missing",
                "",
                "Young player has no usable draft-capital prior row.",
            )
        )
        return
    row["draft_year"] = bridge.get("draft_year", "")
    row["draft_round"] = (
        ""
        if str(bridge.get("nfl_draft_round") or "").upper() == "UDFA"
        else bridge.get("nfl_draft_round", "")
    )
    row["draft_overall"] = bridge.get("nfl_draft_pick", "")
    row["young_nfl_bridge_source"] = "truth_set_v3_draft_capital_prior_preview"
    row["warnings"] = _append_warning(row.get("warnings"), "v3_young_bridge_prior_preview")
    used.append("v3_young_bridge_prior")
    coverage.append(
        _coverage(
            player,
            position,
            "young_bridge_prior",
            "derived_real_data",
            "model_preview_only",
            "covered",
            "draft_year|draft_round|draft_pick|draft_capital_prior_score",
            "Factual draft-capital prior for eligible young players.",
        )
    )


def _apply_injury_context(
    row: dict[str, object],
    injury: dict[str, str] | None,
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    if not injury:
        coverage.append(
            _coverage(
                player,
                position,
                "injury",
                "missing",
                "context_only",
                "missing",
                "",
                "No injury context row matched.",
            )
        )
        return
    if injury.get("source_url") and (
        injury.get("current_injury") or injury.get("body_part") or injury.get("ir_pup_status")
    ):
        row["warnings"] = _append_warning(row.get("warnings"), "v3_sourced_injury_context")
        used.append("v3_sourced_injury_context")
        coverage.append(
            _coverage(
                player,
                position,
                "injury",
                "sourced_context",
                "confidence_context_only",
                "covered_context",
                "current_injury|body_part|ir_pup_status",
                "Sourced injury context retained; no fake healthy boost.",
            )
        )
    else:
        review_flags.append("v3_injury_context_unsourced_or_healthy_not_scored")
        coverage.append(
            _coverage(
                player,
                position,
                "injury",
                "unsourced_or_healthy_context",
                "context_only",
                "review",
                "",
                "Healthy/active statements without source are context only.",
            )
        )


def _apply_market_context(
    row: dict[str, object],
    market: dict[str, str] | None,
    market_score: float | None,
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    if market_score is None or not market:
        review_flags.append("v3_missing_sourced_market_context")
        coverage.append(
            _coverage(
                player,
                position,
                "market_liquidity",
                "missing_market",
                "trade_context_only",
                "missing",
                "",
                "No sourced market value; private/model value unaffected.",
            )
        )
        return
    row["market_liquidity"] = _round(market_score, 50.0)
    used.append("v3_market_context_only")
    coverage.append(
        _coverage(
            player,
            position,
            "market_liquidity",
            "sourced_context",
            "trade_context_only",
            "covered_context",
            "trade_value_number",
            "Market retained as trade/liquidity context only.",
        )
    )


def _apply_route_honesty(
    row: dict[str, object],
    route_status: str,
    used: list[str],
    review_flags: list[str],
    coverage: list[dict[str, object]],
) -> None:
    player = str(row.get("player_name") or "")
    position = str(row.get("position") or "")
    row["route_role"] = 50.0
    used.append("v3_route_values_quarantined")
    if position in {"WR", "TE"}:
        row["warnings"] = _append_warning(
            row.get("warnings"),
            "route_data_unavailable_free_public",
        )
        review_flags.append("v3_route_metrics_unavailable_free_public")
        coverage_status = "review"
        notes = "Free/public route data unavailable; route_role held neutral and flagged."
    else:
        coverage_status = "not_applicable"
        notes = "Route metrics are not used by this position formula; route_role held neutral."
    coverage.append(
        _coverage(
            player,
            position,
            "route_participation",
            route_status or "unavailable_free_public",
            "not_used",
            coverage_status,
            "routes_run|route_participation|tprr|yprr",
            notes,
        )
    )


def _route_status_from_field_contract(rows: list[dict[str, str]]) -> str:
    for row in rows:
        if row.get("field_name") in {"routes_run", "route_participation", "tprr", "yprr"}:
            return row.get("source_status") or "unavailable_free_public"
    return "unavailable_free_public"


def _production_scores(production_by_name: dict[str, dict[str, object]]) -> dict[str, float]:
    ppg_by_pos: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for key, row in production_by_name.items():
        games = max(_float(row.get("games"), 0.0) or 0.0, 1.0)
        points = _lve_points(row)
        ppg_by_pos[str(row.get("position") or "")].append((key, points / games))
    return _normalize_by_position(ppg_by_pos)


def _first_down_scores(production_by_name: dict[str, dict[str, object]]) -> dict[str, float]:
    by_pos: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for key, row in production_by_name.items():
        games = max(_float(row.get("games"), 0.0) or 0.0, 1.0)
        td_points = (
            (_float(row.get("rushing_tds"), 0.0) or 0.0)
            * LVE_SCORING["rushing_td"]
        ) + (
            _float(row.get("receiving_tds"), 0.0) or 0.0
        ) * LVE_SCORING["receiving_td"]
        fd_points = (
            (_float(row.get("rushing_first_downs"), 0.0) or 0.0)
            + (_float(row.get("receiving_first_downs"), 0.0) or 0.0)
        ) * LVE_SCORING["rushing_receiving_first_down"]
        by_pos[str(row.get("position") or "")].append((key, (td_points + fd_points) / games))
    return _normalize_by_position(by_pos)


def _efficiency_scores(production_by_name: dict[str, dict[str, object]]) -> dict[str, float]:
    by_pos: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for key, row in production_by_name.items():
        position = str(row.get("position") or "")
        games = max(_float(row.get("games"), 0.0) or 0.0, 1.0)
        points = _lve_points(row)
        if position == "QB":
            value = points / games
        else:
            opportunities = (_float(row.get("rushing_attempts"), 0.0) or 0.0) + (
                _float(row.get("targets"), 0.0) or 0.0
            )
            value = 0.0 if opportunities <= 0 else points / opportunities
        by_pos[position].append((key, value))
    return _normalize_by_position(by_pos)


def _usage_scores(
    usage_by_name: dict[str, dict[str, object]],
    snap_by_name: dict[str, dict[str, object]],
) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    workload_values: dict[str, list[tuple[str, float]]] = defaultdict(list)
    target_values: dict[str, list[tuple[str, float]]] = defaultdict(list)
    snap_scores: dict[str, float] = {}
    for key, row in usage_by_name.items():
        position = str(row.get("position") or "")
        games = max(_float(row.get("games_with_usage"), 0.0) or 0.0, 1.0)
        weighted_opp_per_game = (_float(row.get("weighted_opportunities"), 0.0) or 0.0) / games
        workload_values[position].append((key, weighted_opp_per_game))
        target_share = _float(row.get("target_share"), 0.0) or 0.0
        rb_target_share = _float(row.get("rb_target_share"), 0.0) or 0.0
        target_values[position].append((key, target_share or rb_target_share))
    workload_scores = _normalize_by_position(workload_values)
    target_scores = _normalize_by_position(target_values)
    for key, row in snap_by_name.items():
        snap_scores[key] = clamp_score((_float(row.get("avg_snap_share"), 0.0) or 0.0) * 100.0)
    for key in set(workload_scores) | set(target_scores) | set(snap_scores):
        workload = workload_scores.get(key, 50.0)
        target = target_scores.get(key, 50.0)
        snap = snap_scores.get(key, 50.0)
        output[key] = {
            "workload_earning": workload,
            "target_earning_stability": target,
            "role_security": round(
                clamp_score((0.45 * snap) + (0.35 * workload) + (0.20 * target)), 2
            ),
        }
    return output


def _projection_scores(rows: list[dict[str, str]]) -> dict[str, float]:
    by_pos: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        if row.get("projection_availability_status") != "projection_stat_line_present":
            continue
        points = _float(row.get("recomputed_lve_points"))
        if points is None:
            continue
        by_pos[str(row.get("position") or "")].append((_name_key(row.get("player_name")), points))
    return _normalize_by_position(by_pos)


def _market_scores(rows: list[dict[str, str]]) -> dict[str, float]:
    pairs = [
        (_name_key(row.get("player_name")), _float(row.get("trade_value_number"))) for row in rows
    ]
    valid = [(key, value) for key, value in pairs if value is not None]
    if not valid:
        return {}
    values = [value for _, value in valid]
    low = min(values)
    high = max(values)
    return {
        key: 50.0
        if high == low
        else round(clamp_score(35.0 + 60.0 * ((value - low) / (high - low))), 2)
        for key, value in valid
    }


def _latest_weighted_by_name(
    rows: list[dict[str, str]],
    name_field: str,
) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_name_key(row.get(name_field) or row.get("player_name"))].append(row)
    output: dict[str, dict[str, object]] = {}
    for key, player_rows in grouped.items():
        sorted_rows = sorted(player_rows, key=lambda row: _float(row.get("season"), 0.0) or 0.0)
        weights = _season_weights(sorted_rows)
        combined: dict[str, object] = dict(sorted_rows[-1])
        for column in set().union(*(row.keys() for row in sorted_rows)):
            values = [
                (_float(row.get(column)), weights[index]) for index, row in enumerate(sorted_rows)
            ]
            if any(value is not None for value, _ in values):
                combined[column] = round(
                    sum((value or 0.0) * weight for value, weight in values),
                    4,
                )
        combined["latest_season"] = sorted_rows[-1].get("season", "")
        output[key] = combined
    return output


def _season_weights(rows: list[dict[str, str]]) -> list[float]:
    raw = [1.0, 2.0, 3.0][-len(rows) :]
    total = sum(raw)
    return [value / total for value in raw]


def _normalize_by_position(values_by_pos: dict[str, list[tuple[str, float]]]) -> dict[str, float]:
    output: dict[str, float] = {}
    for entries in values_by_pos.values():
        if not entries:
            continue
        values = [value for _, value in entries]
        low = min(values)
        high = max(values)
        for key, value in entries:
            output[key] = (
                50.0
                if high == low
                else round(clamp_score(35.0 + 60.0 * ((value - low) / (high - low))), 2)
            )
    return output


def _lve_points(row: dict[str, object]) -> float:
    return (
        (_float(row.get("passing_yards"), 0.0) or 0.0)
        * LVE_SCORING["passing_yard"]
        + (_float(row.get("passing_tds"), 0.0) or 0.0)
        * LVE_SCORING["passing_td"]
        + (_float(row.get("interceptions"), 0.0) or 0.0)
        * LVE_SCORING["interception"]
        + (_float(row.get("rushing_yards"), 0.0) or 0.0)
        * LVE_SCORING["rushing_yard"]
        + (_float(row.get("rushing_tds"), 0.0) or 0.0)
        * LVE_SCORING["rushing_td"]
        + (_float(row.get("receiving_yards"), 0.0) or 0.0)
        * LVE_SCORING["receiving_yard"]
        + (_float(row.get("receiving_tds"), 0.0) or 0.0)
        * LVE_SCORING["receiving_td"]
        + (
            (_float(row.get("rushing_first_downs"), 0.0) or 0.0)
            + (_float(row.get("receiving_first_downs"), 0.0) or 0.0)
        )
        * LVE_SCORING["rushing_receiving_first_down"]
        + (_float(row.get("fumbles_lost"), 0.0) or 0.0)
        * LVE_SCORING["fumble_lost"]
    )


def _movement_rows(
    v2_outputs: list[dict[str, str]],
    v3_outputs: list[dict[str, str]],
    changed_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    v2_by_name = {_name_key(row.get("player_name")): row for row in v2_outputs}
    v3_by_name = {_name_key(row.get("player_name")): row for row in v3_outputs}
    changed_by_name = {_name_key(row.get("player_name")): row for row in changed_rows}
    rows: list[dict[str, object]] = []
    for key, changed in changed_by_name.items():
        v2 = v2_by_name.get(key, {})
        v3 = v3_by_name.get(key, {})
        v2_value = _float(v2.get("private_lve_value"), 0.0) or 0.0
        v3_value = _float(v3.get("private_lve_value"), 0.0) or 0.0
        rows.append(
            {
                "player_name": changed.get("player_name", v3.get("player_name", "")),
                "position": changed.get("position", v3.get("position", "")),
                "v2_overall_rank": v2.get("overall_rank", ""),
                "v3_overall_rank": v3.get("overall_rank", ""),
                "rank_delta": _rank_delta(v2.get("overall_rank"), v3.get("overall_rank")),
                "v2_model_value": round(v2_value, 2),
                "v3_model_value": round(v3_value, 2),
                "model_value_delta": round(v3_value - v2_value, 2),
                "movement_reason": _movement_reason(changed),
                "review_flags": changed.get("truth_set_v3_review_flags", ""),
            }
        )
    return sorted(
        rows, key=lambda row: abs(_float(row.get("model_value_delta"), 0.0) or 0.0), reverse=True
    )


def _movement_reason(row: dict[str, object]) -> str:
    used = _used(row)
    reasons = []
    if "v3_native_production" in used:
        reasons.append("native nflverse production")
    if "v3_derived_usage" in used:
        reasons.append("derived play-by-play usage")
    if "v3_snap_share" in used:
        reasons.append("snap share")
    if "v3_projection_recompute" in used:
        reasons.append("projection recompute")
    if "v3_young_bridge_prior" in used:
        reasons.append("young bridge prior")
    if "v3_route_values_quarantined" in used:
        reasons.append("route values quarantined")
    return "; ".join(reasons) or "no v3 scoring field"


def _rejected_rows(player_name: str, position: str) -> list[dict[str, object]]:
    base = [
        (
            "rejected_agent_production_csv",
            "Malformed/shifted agent CSV remains rejected.",
            "truth_set_lab_v1 production_data.csv",
        ),
        (
            "rejected_agent_role_usage_csv",
            "Malformed/prose role-usage CSV remains rejected.",
            "truth_set_lab_v1 role_usage.csv",
        ),
        (
            "supplied_non_lve_projection_points",
            "Supplied projection points are not LVE scoring and are rejected.",
            "projection source supplied points",
        ),
        (
            "fake_route_values",
            (
                "Routes, route participation, TPRR, and YPRR are unavailable from "
                "free/public structured data."
            ),
            "route defaults",
        ),
    ]
    return [
        {
            "player_name": player_name,
            "position": position,
            "field_group": group,
            "rejection_reason": reason,
            "source": source,
            "model_usage": "not_used",
        }
        for group, reason, source in base
    ]


def _coverage(
    player: str,
    position: str,
    bucket: str,
    source_status: str,
    model_usage: str,
    coverage_status: str,
    fields: str,
    notes: str,
) -> dict[str, object]:
    return {
        "player_name": player,
        "position": position,
        "bucket": bucket,
        "source_status": source_status,
        "model_usage": model_usage,
        "coverage_status": coverage_status,
        "fields": fields,
        "notes": notes,
    }


def _projection_warning_set(flags: str) -> set[str]:
    output = set()
    if "missing_first_down_projection" in flags:
        output.add("projection_first_downs_missing")
    if "team_mismatch" in flags:
        output.add("projection_team_mismatch_review")
    if "missing_projection" in flags:
        output.add("projection_missing_review")
    if "high_active_value_missing_projection" in flags:
        output.add("high_active_value_missing_projection_review")
    return output


def _replace_warnings(value: object, *, remove: set[str], add: set[str]) -> str:
    parts = {part for part in str(value or "").split("|") if part and part not in remove}
    parts.update(add)
    return "|".join(sorted(parts))


def _append_warning(value: object, warning: str) -> str:
    parts = {part for part in str(value or "").split("|") if part}
    parts.add(warning)
    return "|".join(sorted(parts))


def _rank_delta(old: object, new: object) -> object:
    old_rank = _float(old)
    new_rank = _float(new)
    if old_rank is None or new_rank is None:
        return ""
    return int(old_rank - new_rank)


def _used(row: dict[str, object]) -> str:
    return str(row.get("truth_set_v3_source_fields_used") or "")


def _summary_rows(summary: dict[str, object]) -> list[dict[str, object]]:
    return [{"metric": key, "value": value} for key, value in summary.items()]


def _round(value: float | None, default: float) -> float:
    return round(clamp_score(default if value is None else value), 2)


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _name_key(value: object) -> str:
    text = str(value or "").lower().replace("â€™", "'").replace("’", "'")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    if not Path(path).exists():
        return []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    path: str | Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
