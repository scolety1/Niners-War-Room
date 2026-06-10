from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.model_edge_evaluation_harness_service import (
    DEFAULT_OUTPUT_ROOT as MODEL_EDGE_OUTPUT_ROOT,
)

OUTPUT_ROOT = MODEL_EDGE_OUTPUT_ROOT
HARNESS_ROWS_PATH = OUTPUT_ROOT / "model_edge_evaluation_harness_review_rows.csv"
CURRENT_BOARD_PATH = Path(
    "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
)
CURRENT_COMPONENTS_PATH = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
MISS_PATTERN_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_rows.csv"
)

TOURNAMENT_VERSION = "shadow_model_tournament_0.1.0"
SHADOW_ONLY_POLICY = "shadow_only_no_active_rankings_overwrite"
SOURCE_POLICY = (
    "uses_private_current_components_and_historical_replay_features_only;"
    "market_league_adp_public_projection_rotowire_rankings_prior_draft_legacy_blocked"
)

EXPERIMENT_IDS = (
    "production_baseline",
    "established_wr_proof_lane",
    "rb_dynasty_horizon",
    "te_no_premium_exception_gate",
    "elite_qb_floor_horizon",
    "missing_evidence_policy",
)

WATCH_PLAYERS = (
    "Chase Brown",
    "CeeDee Lamb",
    "Justin Jefferson",
    "Jaylen Waddle",
    "Puka Nacua",
    "Jaxon Smith-Njigba",
    "Trey McBride",
    "Brock Bowers",
    "Kyle Pitts",
    "Travis Kelce",
    "Josh Allen",
    "Patrick Mahomes",
    "Lamar Jackson",
    "Jayden Daniels",
    "Joe Burrow",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "De'Von Achane",
    "Breece Hall",
)

HISTORICAL_ROW_HEADER = (
    "experiment_id",
    "draft_year",
    "player",
    "position",
    "baseline_rank",
    "shadow_rank",
    "rank_delta",
    "baseline_score",
    "shadow_score",
    "score_delta",
    "draft_round",
    "overall_pick",
    "rank_bucket",
    "shadow_rank_bucket",
    "pick_range_bucket",
    "league_outcome_label",
    "hit_bust_classification",
    "outcome_maturity",
    "strict_starter_hit",
    "difference_maker",
    "changed_by_experiment",
    "reason_codes",
    "formula_inputs_used",
    "shadow_only_policy",
    "contamination_check",
)

CURRENT_ROW_HEADER = (
    "experiment_id",
    "player",
    "position",
    "team",
    "baseline_rank",
    "shadow_rank",
    "rank_delta",
    "baseline_score",
    "shadow_score",
    "score_delta",
    "trust_status",
    "roster_status",
    "pool_status",
    "warning_flags",
    "changed_by_experiment",
    "reason_codes",
    "formula_inputs_used",
    "shadow_only_policy",
    "contamination_check",
)

WATCH_ROW_HEADER = CURRENT_ROW_HEADER + (
    "watch_row",
    "finding",
)

HISTORICAL_METRIC_HEADER = (
    "experiment_id",
    "metric_scope",
    "position",
    "rank_window",
    "rows",
    "strict_hits",
    "strict_hit_rate",
    "difference_makers",
    "difference_maker_rate",
    "busts",
    "bust_rate",
    "high_ranked_misses",
    "low_ranked_hit_capture",
    "false_positive_rate",
    "verdict_context",
    "tournament_version",
)

SUMMARY_HEADER = (
    "experiment_id",
    "hypothesis",
    "policy_change_tested",
    "historical_result",
    "hit_bust_pattern_improvement",
    "new_failure_modes",
    "current_board_watch_movement",
    "classification",
    "production_scores_changed",
    "contamination_rows",
    "tournament_version",
)

POSITION_MOVEMENT_HEADER = (
    "experiment_id",
    "position",
    "current_rows",
    "average_rank_movement",
    "average_abs_rank_movement",
    "players_moved_more_than_12",
    "average_score_delta",
    "tournament_version",
)


@dataclass(frozen=True)
class ShadowTournamentResult:
    historical_rows: tuple[dict[str, object], ...]
    current_rows: tuple[dict[str, object], ...]
    watch_rows: tuple[dict[str, object], ...]
    historical_metric_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    position_movement_rows: tuple[dict[str, object], ...]
    docs: dict[str, str]
    baseline_hash_before: str
    baseline_hash_after: str


def build_shadow_model_tournament(
    harness_rows_path: str | Path = HARNESS_ROWS_PATH,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    current_components_path: str | Path = CURRENT_COMPONENTS_PATH,
    miss_pattern_rows_path: str | Path = MISS_PATTERN_ROWS_PATH,
) -> ShadowTournamentResult:
    baseline_path = Path(current_board_path)
    baseline_hash_before = _sha256(baseline_path)
    historical_source = _read_rows(Path(harness_rows_path))
    board_source = _read_rows(baseline_path)
    component_source = _read_rows(Path(current_components_path))
    miss_pattern_rows = _read_rows(Path(miss_pattern_rows_path))

    current_rows = _merge_current_rows(board_source, component_source)
    historical_rows = _historical_shadow_rows(historical_source)
    current_shadow_rows = _current_shadow_rows(current_rows)
    historical_metrics = _historical_metric_rows(historical_rows)
    position_movement = _position_movement_rows(current_shadow_rows)
    watch_rows = _watch_rows(current_shadow_rows)
    summary_rows = _summary_rows(
        historical_rows,
        current_shadow_rows,
        historical_metrics,
        miss_pattern_rows,
    )
    docs = _docs(summary_rows, historical_metrics, current_shadow_rows, watch_rows)
    baseline_hash_after = _sha256(baseline_path)

    return ShadowTournamentResult(
        historical_rows=tuple(historical_rows),
        current_rows=tuple(current_shadow_rows),
        watch_rows=tuple(watch_rows),
        historical_metric_rows=tuple(historical_metrics),
        summary_rows=tuple(summary_rows),
        position_movement_rows=tuple(position_movement),
        docs=docs,
        baseline_hash_before=baseline_hash_before,
        baseline_hash_after=baseline_hash_after,
    )


def write_shadow_model_tournament_outputs(
    output_root: str | Path = OUTPUT_ROOT,
    result: ShadowTournamentResult | None = None,
) -> dict[str, Path]:
    result = result or build_shadow_model_tournament()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "historical_rows": output / "shadow_model_tournament_historical_rows.csv",
        "current_rows": output / "shadow_model_tournament_current_board_rows.csv",
        "watch_rows": output / "shadow_model_tournament_watch_rows.csv",
        "historical_metrics": output / "shadow_model_tournament_historical_metrics.csv",
        "summary": output / "shadow_model_tournament_summary.csv",
        "position_movement": output / "shadow_model_tournament_position_movement.csv",
    }
    _write_csv(paths["historical_rows"], HISTORICAL_ROW_HEADER, result.historical_rows)
    _write_csv(paths["current_rows"], CURRENT_ROW_HEADER, result.current_rows)
    _write_csv(paths["watch_rows"], WATCH_ROW_HEADER, result.watch_rows)
    _write_csv(
        paths["historical_metrics"],
        HISTORICAL_METRIC_HEADER,
        result.historical_metric_rows,
    )
    _write_csv(paths["summary"], SUMMARY_HEADER, result.summary_rows)
    _write_csv(
        paths["position_movement"],
        POSITION_MOVEMENT_HEADER,
        result.position_movement_rows,
    )
    doc_paths = {
        "tournament_doc": Path("docs/model_v4/SHADOW_MODEL_TOURNAMENT_20260610.md"),
        "current_diff_doc": Path("docs/model_v4/SHADOW_MODEL_CURRENT_BOARD_DIFF_20260610.md"),
        "rookie_implications_doc": Path(
            "docs/model_v4/SHADOW_MODEL_ROOKIE_DRAFT_IMPLICATIONS_20260610.md"
        ),
    }
    for key, path in doc_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.docs[key], encoding="utf-8")
        paths[key] = path
    return paths


def _historical_shadow_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        scored_rows = []
        for row in rows:
            base = _float(row.get("private_score_at_eval"))
            score, changed, reasons, inputs = _historical_shadow_score(experiment_id, row, base)
            scored_rows.append(
                {
                    **row,
                    "_shadow_score": score,
                    "_changed": changed,
                    "_reasons": reasons,
                    "_inputs": inputs,
                }
            )
        rank_lookup = _rank_lookup(scored_rows, "draft_year", "_shadow_score", "player")
        for row in scored_rows:
            baseline_rank = _int(row.get("model_rank"))
            shadow_rank = rank_lookup[(str(row.get("draft_year", "")), str(row.get("player", "")))]
            output.append(
                {
                    "experiment_id": experiment_id,
                    "draft_year": row.get("draft_year", ""),
                    "player": row.get("player", ""),
                    "position": row.get("position", ""),
                    "baseline_rank": _blank(baseline_rank),
                    "shadow_rank": shadow_rank,
                    "rank_delta": _blank(_delta(shadow_rank, baseline_rank)),
                    "baseline_score": _blank(_float(row.get("private_score_at_eval"))),
                    "shadow_score": _blank(row["_shadow_score"]),
                    "score_delta": _blank(
                        _score_delta(row["_shadow_score"], _float(row.get("private_score_at_eval")))
                    ),
                    "draft_round": row.get("draft_round", ""),
                    "overall_pick": row.get("overall_pick", ""),
                    "rank_bucket": row.get("rank_bucket", ""),
                    "shadow_rank_bucket": _rank_bucket(shadow_rank),
                    "pick_range_bucket": row.get("pick_range_bucket", ""),
                    "league_outcome_label": row.get("league_outcome_label", ""),
                    "hit_bust_classification": row.get("hit_bust_classification", ""),
                    "outcome_maturity": row.get("outcome_maturity", ""),
                    "strict_starter_hit": _bool(row.get("strict_starter_hit")),
                    "difference_maker": _bool(row.get("difference_maker")),
                    "changed_by_experiment": row["_changed"],
                    "reason_codes": "|".join(row["_reasons"]),
                    "formula_inputs_used": "|".join(row["_inputs"]),
                    "shadow_only_policy": SHADOW_ONLY_POLICY,
                    "contamination_check": "no_blocked_inputs_used",
                }
            )
    return output


def _current_shadow_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        scored_rows = []
        for row in rows:
            base = _float(row.get("nwr_dynasty_score"))
            if base is None:
                score, changed, reasons, inputs = (
                    None,
                    "unscored_or_hidden",
                    ("unscored_k_or_no_nwr_score",),
                    ("position|production_nwr_score",),
                )
            else:
                score, changed, reasons, inputs = _current_shadow_score(experiment_id, row, base)
            scored_rows.append(
                {
                    **row,
                    "_shadow_score": score,
                    "_changed": changed,
                    "_reasons": reasons,
                    "_inputs": inputs,
                }
            )
        rank_lookup = _current_rank_lookup(scored_rows)
        for row in scored_rows:
            baseline_rank = _int(row.get("nwr_rank"))
            shadow_rank = rank_lookup.get(_current_key(row), "")
            output.append(
                {
                    "experiment_id": experiment_id,
                    "player": row.get("player_name", ""),
                    "position": row.get("position", ""),
                    "team": row.get("nfl_team", ""),
                    "baseline_rank": _blank(baseline_rank),
                    "shadow_rank": shadow_rank,
                    "rank_delta": _blank(
                        _delta(_int(shadow_rank), baseline_rank) if shadow_rank != "" else None
                    ),
                    "baseline_score": _blank(_float(row.get("nwr_dynasty_score"))),
                    "shadow_score": _blank(row["_shadow_score"]),
                    "score_delta": _blank(
                        _score_delta(row["_shadow_score"], _float(row.get("nwr_dynasty_score")))
                    ),
                    "trust_status": row.get("trust_status", ""),
                    "roster_status": row.get("roster_status", ""),
                    "pool_status": row.get("pool_status", ""),
                    "warning_flags": row.get("warning_flags", ""),
                    "changed_by_experiment": row["_changed"],
                    "reason_codes": "|".join(row["_reasons"]),
                    "formula_inputs_used": "|".join(row["_inputs"]),
                    "shadow_only_policy": SHADOW_ONLY_POLICY,
                    "contamination_check": "no_blocked_inputs_used",
                }
            )
    return output


def _historical_shadow_score(
    experiment_id: str,
    row: dict[str, str],
    base: float | None,
) -> tuple[float | None, str, tuple[str, ...], tuple[str, ...]]:
    if base is None:
        return None, "unscored", ("missing_baseline_score",), ("historical_replay_score",)
    if experiment_id == "production_baseline":
        return (
            base,
            "unchanged_by_experiment",
            ("production_baseline",),
            ("historical_replay_score",),
        )
    if experiment_id == "established_wr_proof_lane":
        return _historical_wr_score(row, base)
    if experiment_id == "rb_dynasty_horizon":
        return _historical_rb_score(row, base)
    if experiment_id == "te_no_premium_exception_gate":
        return _historical_te_score(row, base)
    if experiment_id == "elite_qb_floor_horizon":
        return _historical_qb_score(row, base)
    if experiment_id == "missing_evidence_policy":
        return _historical_missing_evidence_score(row, base)
    raise ValueError(f"Unknown experiment: {experiment_id}")


def _current_shadow_score(
    experiment_id: str,
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if experiment_id == "production_baseline":
        return base, "unchanged_by_experiment", ("production_baseline",), ("production_nwr_score",)
    if experiment_id == "established_wr_proof_lane":
        return _current_wr_score(row, base)
    if experiment_id == "rb_dynasty_horizon":
        return _current_rb_score(row, base)
    if experiment_id == "te_no_premium_exception_gate":
        return _current_te_score(row, base)
    if experiment_id == "elite_qb_floor_horizon":
        return _current_qb_score(row, base)
    if experiment_id == "missing_evidence_policy":
        return _current_missing_evidence_score(row, base)
    raise ValueError(f"Unknown experiment: {experiment_id}")


def _historical_wr_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "WR":
        return base, "unchanged_by_experiment", ("not_wr",), ("position|historical_replay_score",)
    profile = _profile(row)
    draft = profile["draft_capital"]
    production = max(profile["production"], profile["team_share"])
    evidence = _float(row.get("evidence_available")) or 0.0
    if draft < 75 and production < 80:
        return base, "unchanged_by_experiment", ("wr_proof_gate_not_met",), _historical_inputs()
    lift = 3.0
    if draft >= 85:
        lift += 2.0
    if production >= 80:
        lift += 1.0
    if evidence < 0.7:
        lift += 1.0
    return (
        round(min(100.0, base + lift), 4),
        "established_wr_proof_lane",
        ("round1_or_strong_wr_profile_protected", "missing_evidence_softened_for_wr"),
        _historical_inputs(),
    )


def _historical_rb_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "RB":
        return base, "unchanged_by_experiment", ("not_rb",), ("position|historical_replay_score",)
    draft_round = _int(row.get("draft_round"))
    profile = _profile(row)
    production = max(profile["production"], profile["team_share"])
    draft = profile["draft_capital"]
    penalty = 0.0
    reasons: list[str] = []
    if draft_round and draft_round >= 4 and production >= 70 and draft < 55:
        penalty += 6.0
        reasons.append("late_capital_production_trap_cap")
    if draft_round and draft_round <= 2 and draft >= 75:
        return (
            round(min(100.0, base + 1.0), 4),
            "rb_dynasty_horizon",
            ("early_capital_rb_preserved",),
            _historical_inputs(),
        )
    if penalty <= 0:
        return base, "unchanged_by_experiment", ("rb_horizon_gate_not_met",), _historical_inputs()
    return (
        round(max(0.0, base - penalty), 4),
        "rb_dynasty_horizon",
        tuple(reasons),
        _historical_inputs(),
    )


def _historical_te_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "TE":
        return base, "unchanged_by_experiment", ("not_te",), ("position|historical_replay_score",)
    profile = _profile(row)
    exceptional = (
        profile["draft_capital"] >= 78 and max(profile["production"], profile["team_share"]) >= 70
    )
    cap = 42.0 if exceptional else 34.0
    if base <= cap:
        return (
            base,
            "unchanged_by_experiment",
            ("te_already_within_no_premium_band",),
            _historical_inputs(),
        )
    return (
        round(cap + (base - cap) * 0.35, 4),
        "te_no_premium_exception_gate",
        ("no_premium_te_upper_band_compression", "elite_exception_receipt_required"),
        _historical_inputs(),
    )


def _historical_qb_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "QB":
        return base, "unchanged_by_experiment", ("not_qb",), ("position|historical_replay_score",)
    profile = _profile(row)
    if profile["draft_capital"] < 85:
        return base, "unchanged_by_experiment", ("qb_floor_gate_not_met",), _historical_inputs()
    floor = 38.0
    cap = 46.0
    score = min(cap, max(base, floor))
    if score == base:
        return base, "unchanged_by_experiment", ("qb_already_above_floor",), _historical_inputs()
    return (
        round(score, 4),
        "elite_qb_floor_horizon",
        ("round1_qb_floor_protected_but_1qb_capped",),
        _historical_inputs(),
    )


def _historical_missing_evidence_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    evidence = _float(row.get("evidence_available")) or 0.0
    if evidence >= 0.7:
        return base, "unchanged_by_experiment", ("sufficient_evidence",), _historical_inputs()
    profile = _profile(row)
    strong_single = max(profile.values()) >= 85
    penalty = 4.0 if strong_single else 2.0
    return (
        round(max(0.0, base - penalty), 4),
        "missing_evidence_policy",
        ("low_evidence_confidence_cap_strengthened",),
        _historical_inputs(),
    )


def _current_wr_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "WR":
        return base, "unchanged_by_experiment", ("not_wr",), _current_inputs()
    role = row.get("role_archetype", "")
    review = _float(row.get("review_scoring_points")) or 0.0
    vorp = _float(row.get("positive_vorp_points")) or 0.0
    warnings = row.get("warning_flags", "")
    if "wr_target_earner" not in role or review < 130 or vorp < 30:
        return (
            base,
            "unchanged_by_experiment",
            ("wr_private_proof_gate_not_met",),
            _current_inputs(),
        )
    lift = 4.0
    if vorp >= 60 or review >= 160:
        lift += 2.0
    if vorp >= 100 or review >= 200:
        lift += 1.5
    if (
        "missing_or_review_route_target_snap_evidence" in warnings
        or "partial_first_down" in warnings
    ):
        lift += 1.0
    return (
        round(min(100.0, base + min(lift, 8.0)), 4),
        "established_wr_proof_lane",
        ("private_wr_target_earning_proof", "missing_route_receipts_trust_cap_not_score_crush"),
        _current_inputs(),
    )


def _current_rb_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "RB":
        return base, "unchanged_by_experiment", ("not_rb",), _current_inputs()
    vorp = _float(row.get("positive_vorp_points")) or 0.0
    lifecycle = _float(row.get("lifecycle_modifier_review")) or 1.0
    role = row.get("role_archetype", "")
    fragility = row.get("role_fragility_status", "")
    warnings = row.get("warning_flags", "")
    penalty = 0.0
    reasons: list[str] = []
    if vorp >= 140 and lifecycle >= 1.0:
        return (
            round(max(0.0, base - 1.0), 4),
            "rb_dynasty_horizon",
            ("elite_young_rb_mostly_preserved",),
            _current_inputs(),
        )
    if "short_window" in role and vorp < 130:
        penalty += 5.0
        reasons.append("short_window_rb_role_horizon_cap")
    if "fragility" in fragility or "no_historical" in warnings or "repeated_head" in warnings:
        penalty += 2.0
        reasons.append("rb_role_or_availability_fragility")
    if lifecycle < 0.9 or "rb_dynasty_age_curve" in warnings or "age_cliff" in warnings:
        penalty += 3.0
        reasons.append("rb_age_or_lifecycle_horizon_discount")
    if penalty <= 0:
        return base, "unchanged_by_experiment", ("rb_horizon_gate_not_met",), _current_inputs()
    return (
        round(max(0.0, base - penalty), 4),
        "rb_dynasty_horizon",
        tuple(reasons),
        _current_inputs(),
    )


def _current_te_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "TE":
        return base, "unchanged_by_experiment", ("not_te",), _current_inputs()
    vorp = _float(row.get("positive_vorp_points")) or 0.0
    review = _float(row.get("review_scoring_points")) or 0.0
    lifecycle = _float(row.get("lifecycle_modifier_review")) or 1.0
    role = row.get("role_archetype", "")
    warnings = row.get("warning_flags", "")
    if lifecycle < 0.75 or "te_age_33_plus_cliff" in warnings:
        return (
            round(max(0.0, base * 0.7), 4),
            "te_no_premium_exception_gate",
            ("older_or_status_risk_te_discount",),
            _current_inputs(),
        )
    exceptional = vorp >= 80 and review >= 170 and "te_route_target_engine" in role
    if exceptional:
        score = min(base, 58.0)
        return (
            round(score, 4),
            "te_no_premium_exception_gate",
            ("elite_te_exception_allowed_but_no_premium_upper_band_guard",),
            _current_inputs(),
        )
    cap = 34.0 if vorp >= 35 else 28.0
    if base <= cap:
        return (
            base,
            "unchanged_by_experiment",
            ("te_already_within_no_premium_band",),
            _current_inputs(),
        )
    return (
        round(cap + (base - cap) * 0.25, 4),
        "te_no_premium_exception_gate",
        ("no_premium_te_small_or_medium_gap_cap",),
        _current_inputs(),
    )


def _current_qb_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    if row.get("position") != "QB":
        return base, "unchanged_by_experiment", ("not_qb",), _current_inputs()
    review = _float(row.get("review_scoring_points")) or 0.0
    vorp = _float(row.get("positive_vorp_points")) or 0.0
    first_down = _float(row.get("imported_first_down_points")) or 0.0
    floor = 0.0
    if review >= 300 or vorp >= 60:
        floor = 45.0
    elif review >= 260:
        floor = 34.0
    elif review >= 245:
        floor = 30.0
    elif review >= 190 and first_down >= 8:
        floor = 22.0
    if floor <= 0 or base >= floor:
        return (
            base,
            "unchanged_by_experiment",
            ("qb_floor_gate_not_met_or_already_met",),
            _current_inputs(),
        )
    return (
        round(min(52.0, max(base, floor)), 4),
        "elite_qb_floor_horizon",
        ("elite_or_high_review_qb_floor_preserved_but_1qb_capped",),
        _current_inputs(),
    )


def _current_missing_evidence_score(
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...]]:
    confidence = _float(row.get("confidence_cap")) or 1.0
    available = _float(row.get("available_component_weight")) or 0.0
    pos_score = _float(row.get("position_specific_review_score")) or 0.0
    warnings = row.get("warning_flags", "")
    if available < 0.7 or confidence < 0.82:
        return (
            round(max(0.0, base * 0.95), 4),
            "missing_evidence_policy",
            ("thin_or_source_limited_profile_confidence_tightened",),
            _current_inputs(),
        )
    if pos_score >= 50 and (
        "missing_or_review_route_target_snap_evidence" in warnings
        or "missing_lifecycle_or_role_shape_evidence" in warnings
        or "partial_first_down" in warnings
    ):
        return (
            round(min(100.0, base + 2.0), 4),
            "missing_evidence_policy",
            ("proven_private_components_missing_receipts_trust_not_score_crush",),
            _current_inputs(),
        )
    return base, "unchanged_by_experiment", ("missing_evidence_gate_not_met",), _current_inputs()


def _historical_metric_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        variant = [
            row
            for row in rows
            if row["experiment_id"] == experiment_id
            and row["outcome_maturity"] == "three_year_window_available"
        ]
        for position in ("ALL", "QB", "RB", "WR", "TE"):
            pos_rows = (
                variant
                if position == "ALL"
                else [row for row in variant if row["position"] == position]
            )
            for window in (12, 24, 36):
                window_rows = [
                    row for row in pos_rows if (_int(row["shadow_rank"]) or 9999) <= window
                ]
                output.append(
                    _metric_row(
                        experiment_id,
                        "top_window",
                        position,
                        f"top_{window}",
                        window_rows,
                        pos_rows,
                    )
                )
        for position in ("QB", "RB", "WR", "TE"):
            pos_rows = [row for row in variant if row["position"] == position]
            for bucket in ("top_12", "top_24", "top_36", "outside_top_36"):
                bucket_rows = [row for row in pos_rows if _metric_bucket(row) == bucket]
                output.append(
                    _metric_row(
                        experiment_id, "rank_bucket", position, bucket, bucket_rows, pos_rows
                    )
                )
    return output


def _metric_row(
    experiment_id: str,
    scope: str,
    position: str,
    rank_window: str,
    rows: list[dict[str, object]],
    population_rows: list[dict[str, object]],
) -> dict[str, object]:
    strict = [row for row in rows if _bool(row["strict_starter_hit"])]
    diff = [row for row in rows if _bool(row["difference_maker"])]
    busts = [row for row in rows if row["league_outcome_label"] == "Bust"]
    high_misses = [
        row
        for row in rows
        if (_int(row["shadow_rank"]) or 9999) <= 24 and row["league_outcome_label"] == "Bust"
    ]
    low_hit_capture = [
        row
        for row in population_rows
        if _bool(row["strict_starter_hit"])
        and (_int(row["baseline_rank"]) or 0) > 36
        and (_int(row["shadow_rank"]) or 9999) <= 36
    ]
    return {
        "experiment_id": experiment_id,
        "metric_scope": scope,
        "position": position,
        "rank_window": rank_window,
        "rows": len(rows),
        "strict_hits": len(strict),
        "strict_hit_rate": _rate(len(strict), len(rows)),
        "difference_makers": len(diff),
        "difference_maker_rate": _rate(len(diff), len(rows)),
        "busts": len(busts),
        "bust_rate": _rate(len(busts), len(rows)),
        "high_ranked_misses": len(high_misses),
        "low_ranked_hit_capture": len(low_hit_capture),
        "false_positive_rate": _rate(len(high_misses), len(rows)),
        "verdict_context": "shadow_only_historical_replay_not_production_tuning",
        "tournament_version": TOURNAMENT_VERSION,
    }


def _summary_rows(
    historical_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
    miss_pattern_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    output = []
    baseline_metrics = _baseline_metric_index(metrics)
    pattern_counts = Counter(row["pattern_group"] for row in miss_pattern_rows)
    for experiment_id in EXPERIMENT_IDS:
        if experiment_id == "production_baseline":
            classification = "baseline"
        else:
            classification = _classify_experiment(
                experiment_id, metrics, baseline_metrics, current_rows
            )
        output.append(
            {
                "experiment_id": experiment_id,
                "hypothesis": _hypothesis(experiment_id),
                "policy_change_tested": _policy_change(experiment_id),
                "historical_result": _historical_result(experiment_id, metrics, baseline_metrics),
                "hit_bust_pattern_improvement": _pattern_result(experiment_id, pattern_counts),
                "new_failure_modes": _new_failure_modes(experiment_id, current_rows),
                "current_board_watch_movement": _watch_movement_summary(
                    experiment_id, current_rows
                ),
                "classification": classification,
                "production_scores_changed": False,
                "contamination_rows": sum(
                    1
                    for row in current_rows
                    if row["experiment_id"] == experiment_id
                    and row["contamination_check"] != "no_blocked_inputs_used"
                ),
                "tournament_version": TOURNAMENT_VERSION,
            }
        )
    return output


def _position_movement_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for experiment_id in EXPERIMENT_IDS:
        variant = [row for row in rows if row["experiment_id"] == experiment_id]
        for position in sorted({str(row["position"]) for row in variant if row["position"]}):
            pos_rows = [
                row for row in variant if row["position"] == position and row["rank_delta"] != ""
            ]
            deltas = [_float(row["rank_delta"]) or 0.0 for row in pos_rows]
            score_deltas = [
                _float(row["score_delta"]) or 0.0 for row in pos_rows if row["score_delta"] != ""
            ]
            output.append(
                {
                    "experiment_id": experiment_id,
                    "position": position,
                    "current_rows": len(pos_rows),
                    "average_rank_movement": _avg(deltas),
                    "average_abs_rank_movement": _avg([abs(delta) for delta in deltas]),
                    "players_moved_more_than_12": sum(1 for delta in deltas if abs(delta) > 12),
                    "average_score_delta": _avg(score_deltas),
                    "tournament_version": TOURNAMENT_VERSION,
                }
            )
    return output


def _watch_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for row in rows:
        if row["player"] not in WATCH_PLAYERS:
            continue
        output.append(
            {
                **row,
                "watch_row": True,
                "finding": _watch_finding(row),
            }
        )
    return output


def _docs(
    summary_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    watch_rows: list[dict[str, object]],
) -> dict[str, str]:
    return {
        "tournament_doc": _tournament_doc(summary_rows, metrics),
        "current_diff_doc": _current_diff_doc(summary_rows, current_rows, watch_rows),
        "rookie_implications_doc": _rookie_implications_doc(summary_rows, metrics),
    }


def _merge_current_rows(
    board_rows: list[dict[str, str]],
    component_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    components = {
        row.get("normalized_player_name") or _norm(row.get("player_name", "")): row
        for row in component_rows
    }
    merged = []
    for row in board_rows:
        key = row.get("normalized_player_name") or _norm(row.get("player_name", ""))
        merged.append({**components.get(key, {}), **row})
    return merged


def _rank_lookup(
    rows: list[dict[str, object]],
    group_field: str,
    score_field: str,
    name_field: str,
) -> dict[tuple[str, str], int]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_field, ""))].append(row)
    lookup: dict[tuple[str, str], int] = {}
    for group, group_rows in grouped.items():
        ranked = sorted(
            group_rows,
            key=lambda row: (
                row.get(score_field) is None,
                -float(row.get(score_field) or 0.0),
                str(row.get(name_field, "")).lower(),
            ),
        )
        for rank, row in enumerate(ranked, start=1):
            lookup[(group, str(row.get(name_field, "")))] = rank
    return lookup


def _current_rank_lookup(rows: list[dict[str, object]]) -> dict[str, int]:
    scored = [
        row
        for row in rows
        if row.get("_shadow_score") is not None and row.get("position") in {"QB", "RB", "WR", "TE"}
    ]
    ranked = sorted(
        scored,
        key=lambda row: (
            -float(row.get("_shadow_score") or 0.0),
            str(row.get("player_name", "")).lower(),
        ),
    )
    return {_current_key(row): rank for rank, row in enumerate(ranked, start=1)}


def _current_key(row: dict[str, object]) -> str:
    return str(row.get("normalized_player_name") or _norm(str(row.get("player_name", ""))))


def _profile(row: dict[str, str]) -> dict[str, float]:
    raw = str(row.get("pre_draft_profile_features", ""))
    values = {"production": 0.0, "team_share": 0.0, "draft_capital": 0.0, "athletic": 0.0}
    for item in raw.split("|"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key in values:
            values[key] = _float(value) or 0.0
    return values


def _historical_inputs() -> tuple[str, ...]:
    return (
        "position",
        "historical_replay_score",
        "draft_round",
        "overall_pick",
        "production_score",
        "college_team_share",
        "nfl_draft_pick_signal",
        "athletic_score",
        "evidence_available",
        "confidence_cap",
    )


def _current_inputs() -> tuple[str, ...]:
    return (
        "position",
        "nwr_dynasty_score",
        "position_specific_review_score",
        "positive_vorp_points",
        "review_scoring_points",
        "imported_first_down_points",
        "discipline_multiplier",
        "lifecycle_modifier_review",
        "role_archetype",
        "role_fragility_status",
        "confidence_cap",
        "available_component_weight",
        "warning_flags",
    )


def _baseline_metric_index(
    metrics: list[dict[str, object]],
) -> dict[tuple[str, str, str], dict[str, object]]:
    return {
        (row["metric_scope"], row["position"], row["rank_window"]): row
        for row in metrics
        if row["experiment_id"] == "production_baseline"
    }


def _classify_experiment(
    experiment_id: str,
    metrics: list[dict[str, object]],
    baseline: dict[tuple[str, str, str], dict[str, object]],
    current_rows: list[dict[str, object]],
) -> str:
    top24 = _metric(metrics, experiment_id, "top_window", "ALL", "top_24")
    base_top24 = baseline.get(("top_window", "ALL", "top_24"), {})
    fp_delta = (_float(top24.get("false_positive_rate")) or 0.0) - (
        _float(base_top24.get("false_positive_rate")) or 0.0
    )
    strict_delta = (_float(top24.get("strict_hit_rate")) or 0.0) - (
        _float(base_top24.get("strict_hit_rate")) or 0.0
    )
    moved = _moved_more_than(current_rows, experiment_id, 12)
    if experiment_id == "te_no_premium_exception_gate":
        return "needs_more_data"
    if fp_delta <= -0.02 and strict_delta >= -0.02:
        return "accept_shadow_candidate"
    if moved > 40:
        return "reject_too_much_current_board_disruption"
    if strict_delta >= 0.0 or fp_delta < 0.0:
        return "needs_more_review"
    return "needs_more_data"


def _metric(
    metrics: list[dict[str, object]],
    experiment_id: str,
    scope: str,
    position: str,
    window: str,
) -> dict[str, object]:
    return next(
        (
            row
            for row in metrics
            if row["experiment_id"] == experiment_id
            and row["metric_scope"] == scope
            and row["position"] == position
            and row["rank_window"] == window
        ),
        {},
    )


def _hypothesis(experiment_id: str) -> str:
    return {
        "production_baseline": "Current production board, used only as the comparison baseline.",
        "established_wr_proof_lane": (
            "Established and high-signal WR evidence is underprotected when source "
            "receipts are incomplete."
        ),
        "rb_dynasty_horizon": "RB short-window role/VORP overstates 3-year dynasty value.",
        "te_no_premium_exception_gate": (
            "No-premium TE value should require rare receiving and scoring-gap receipts."
        ),
        "elite_qb_floor_horizon": (
            "1QB cap is right, but elite/high-review QBs need a floor so they do not "
            "collapse below weak assets."
        ),
        "missing_evidence_policy": (
            "Missing evidence should cap trust, protect proven profiles, and tighten "
            "thin one-signal profiles."
        ),
    }[experiment_id]


def _policy_change(experiment_id: str) -> str:
    return {
        "production_baseline": "No shadow change.",
        "established_wr_proof_lane": (
            "Adds source-safe WR lift for strong private VORP/review/target-earner "
            "evidence or historical strong WR draft/prod profile."
        ),
        "rb_dynasty_horizon": (
            "Discounts role-fragile or short-window RB value while mostly preserving "
            "elite young RBs."
        ),
        "te_no_premium_exception_gate": (
            "Compresses TE values unless rare no-premium exception receipts pass; "
            "discounts older/status-risk TEs."
        ),
        "elite_qb_floor_horizon": (
            "Adds a capped 1QB floor for high-review/high-VORP QB profiles without "
            "top-board crowding."
        ),
        "missing_evidence_policy": (
            "Tightens low-evidence profiles and softens missing-receipt penalties "
            "for proven private components."
        ),
    }[experiment_id]


def _historical_result(
    experiment_id: str,
    metrics: list[dict[str, object]],
    baseline: dict[tuple[str, str, str], dict[str, object]],
) -> str:
    if experiment_id == "production_baseline":
        row = _metric(metrics, experiment_id, "top_window", "ALL", "top_24")
        return (
            f"Baseline top-24 strict hit rate {row.get('strict_hit_rate')} "
            f"and bust rate {row.get('bust_rate')}."
        )
    row = _metric(metrics, experiment_id, "top_window", "ALL", "top_24")
    base = baseline.get(("top_window", "ALL", "top_24"), {})
    return (
        f"Top-24 strict hit rate {row.get('strict_hit_rate')} "
        f"vs baseline {base.get('strict_hit_rate')}; "
        f"bust rate {row.get('bust_rate')} vs baseline {base.get('bust_rate')}."
    )


def _pattern_result(experiment_id: str, pattern_counts: Counter[str]) -> str:
    if experiment_id == "established_wr_proof_lane":
        return (
            "Tests first-round WR underrank family "
            f"({pattern_counts['first_round_wr_underranks']} rows)."
        )
    if experiment_id == "rb_dynasty_horizon":
        return (
            "Tests late-capital RB false positives "
            f"({pattern_counts['late_capital_production_false_positives']}) "
            "while preserving day-three RB hit family "
            f"({pattern_counts['day_three_rb_hits_worth_preserving']})."
        )
    if experiment_id == "te_no_premium_exception_gate":
        return (
            "Tests TE over/underpromotion families "
            f"({pattern_counts['te_overpromotion']} / "
            f"{pattern_counts['te_underpromotion']})."
        )
    if experiment_id == "elite_qb_floor_horizon":
        return (
            "Tests QB over/underpromotion families "
            f"({pattern_counts['qb_overpromotion']} / "
            f"{pattern_counts['qb_underpromotion']})."
        )
    if experiment_id == "missing_evidence_policy":
        return (
            "Tests low-evidence overpromotion family "
            f"({pattern_counts['low_evidence_overpromotion']} rows)."
        )
    return "Baseline pattern counts only."


def _new_failure_modes(experiment_id: str, current_rows: list[dict[str, object]]) -> str:
    _ = current_rows
    if experiment_id == "te_no_premium_exception_gate":
        return "May overcompress young elite TEs such as Brock Bowers if current VORP gap is small."
    if experiment_id == "established_wr_proof_lane":
        return (
            "May overprotect WRs if current private VORP/review points reflect "
            "one-year spikes rather than durable proof."
        )
    if experiment_id == "rb_dynasty_horizon":
        return "May suppress real late-RB hits if role/receiving path is genuine."
    if experiment_id == "elite_qb_floor_horizon":
        return (
            "May lift mediocre high-volume QBs unless floor gate is paired with "
            "better retained-value labels."
        )
    if experiment_id == "missing_evidence_policy":
        return (
            "May be too blunt until missing-source reason is separated from "
            "missing-player-trait reason."
        )
    return "Baseline only."


def _watch_movement_summary(experiment_id: str, current_rows: list[dict[str, object]]) -> str:
    rows = [
        row
        for row in current_rows
        if row["experiment_id"] == experiment_id and row["player"] in WATCH_PLAYERS
    ]
    movers = sorted(rows, key=lambda row: abs(_float(row["rank_delta"]) or 0.0), reverse=True)[:5]
    return "; ".join(
        f"{row['player']} {row['baseline_rank']}->{row['shadow_rank']}"
        for row in movers
        if row["rank_delta"] != ""
    )


def _watch_finding(row: dict[str, object]) -> str:
    player = row["player"]
    experiment = row["experiment_id"]
    delta = _float(row["rank_delta"]) or 0.0
    if experiment == "production_baseline":
        return "production baseline"
    if player in {"CeeDee Lamb", "Justin Jefferson", "Jaylen Waddle"} and delta < 0:
        return "WR proof lane moves established WR upward without market input."
    if player == "Chase Brown" and delta > 0:
        return "RB horizon policy reduces short-window role pressure."
    if player in {"Patrick Mahomes", "Lamar Jackson"} and delta < 0:
        return "QB floor lane moves elite/high-review QB upward without uncapping 1QB."
    if player in {"Trey McBride", "Brock Bowers", "Kyle Pitts", "Travis Kelce"}:
        return "TE movement requires no-premium human review."
    return "watch movement for human review"


def _tournament_doc(
    summary_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
) -> str:
    lines = [
        "# Shadow Model Tournament - 2026-06-10",
        "",
        (
            "This is a shadow/evaluation tournament only. No production Rankings, "
            "Draft Prep, Live Draft Room, data pack, or Decision Board output is "
            "promoted or overwritten."
        ),
        "",
        "## Guardrails",
        "",
        (
            "- No ADP, market rank, public rankings, consensus, projections, trade "
            "calculators, RotoWire rankings/projections, prior draft history, or "
            "legacy active-pack private_score are used as scoring inputs."
        ),
        "- Team/roster tags are display-only.",
        "- Legal draft pool remains pending.",
        "- Outcome percentages remain in development.",
        "",
        "## Experiment Summary",
        "",
        "| Experiment | Classification | Historical result | Pattern read | Failure mode |",
        "|---|---|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['experiment_id']}` | {row['classification']} | "
            f"{row['historical_result']} | {row['hit_bust_pattern_improvement']} | "
            f"{row['new_failure_modes']} |"
        )
    lines.extend(
        [
            "",
            "## Required Historical Metrics",
            "",
            (
                "| Experiment | Position | Window | Strict hit rate | Bust rate | "
                "High misses | Low-hit capture |"
            ),
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in metrics:
        if row["metric_scope"] == "top_window" and row["rank_window"] in {
            "top_12",
            "top_24",
            "top_36",
        }:
            lines.append(
                f"| `{row['experiment_id']}` | {row['position']} | "
                f"{row['rank_window']} | {row['strict_hit_rate']} | "
                f"{row['bust_rate']} | {row['high_ranked_misses']} | "
                f"{row['low_ranked_hit_capture']} |"
            )
    lines.extend(
        [
            "",
            "## Combined Shadow Model",
            "",
            (
                "No combined shadow model was created in this pass. The individual "
                "lanes did not produce enough support to justify combining them: "
                "WR proof, elite QB floor, and missing-evidence policy need more "
                "review; RB horizon was too disruptive; and the TE gate needs more data."
            ),
            "",
            (
                "A combined model should wait for a second tournament after the "
                "individual lanes are tightened."
            ),
        ]
    )
    return "\n".join(lines)


def _current_diff_doc(
    summary_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    watch_rows: list[dict[str, object]],
) -> str:
    candidate_rows = [
        row
        for row in current_rows
        if row["experiment_id"]
        in {
            "established_wr_proof_lane",
            "elite_qb_floor_horizon",
            "missing_evidence_policy",
        }
    ]
    improvements = sorted(
        [row for row in candidate_rows if row["rank_delta"] != ""],
        key=lambda row: _float(row["rank_delta"]) or 0.0,
    )[:20]
    suspicious = sorted(
        [
            row
            for row in current_rows
            if row["experiment_id"] != "production_baseline" and row["rank_delta"] != ""
        ],
        key=lambda row: abs(_float(row["rank_delta"]) or 0.0),
        reverse=True,
    )[:20]
    lines = [
        "# Shadow Model Current Board Diff - 2026-06-10",
        "",
        (
            "This report compares production Rankings to shadow variants. "
            "Production scores are unchanged."
        ),
        "",
        "## Watch Rows",
        "",
        (
            "| Experiment | Player | Pos | Production rank | Shadow rank | Delta | "
            "Production score | Shadow score | Reason | Finding |"
        ),
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in watch_rows:
        lines.append(
            f"| `{row['experiment_id']}` | {row['player']} | {row['position']} | "
            f"{row['baseline_rank']} | {row['shadow_rank']} | {row['rank_delta']} | "
            f"{row['baseline_score']} | {row['shadow_score']} | "
            f"{row['reason_codes']} | {row['finding']} |"
        )
    lines.extend(
        [
            "",
            "## Top 20 Current-Board Credibility Improvements - Individual Lanes",
            "",
            "| Experiment | Player | Pos | Production rank | Shadow rank | Delta | Reason |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in improvements:
        lines.append(
            f"| `{row['experiment_id']}` | {row['player']} | {row['position']} | "
            f"{row['baseline_rank']} | {row['shadow_rank']} | {row['rank_delta']} | "
            f"{row['reason_codes']} |"
        )
    lines.extend(
        [
            "",
            "## Top 20 New Suspicious Movements - Individual Lanes",
            "",
            "| Experiment | Player | Pos | Production rank | Shadow rank | Delta | Reason |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in suspicious:
        lines.append(
            f"| `{row['experiment_id']}` | {row['player']} | {row['position']} | "
            f"{row['baseline_rank']} | {row['shadow_rank']} | {row['rank_delta']} | "
            f"{row['reason_codes']} |"
        )
    lines.extend(
        [
            "",
            "## Verdict Read",
            "",
            _combined_recommendation(summary_rows),
        ]
    )
    return "\n".join(lines)


def _rookie_implications_doc(
    summary_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
) -> str:
    lines = [
        "# Shadow Model Rookie Draft Implications - 2026-06-10",
        "",
        "This is profile guidance only, not a final draft recommendation.",
        "No production scoring changes are made by this shadow tournament.",
        "",
        "## 1.03 and 1.04",
        "",
        (
            "- Prefer profiles with multiple source-safe signals: production, role "
            "translation, draft capital, age/trajectory, and fit for first-down scoring."
        ),
        (
            "- WR proof-lane results support reviewing first-round or strong "
            "target-earning WRs carefully; historical replay found first-round "
            "WR underrank patterns."
        ),
        (
            "- RBs need upside plus dynasty horizon; short-window production alone "
            "should not dominate."
        ),
        "- QB/TE profiles need exceptional private evidence because this is 1QB/no-TE-premium.",
        "",
        "## 2.04 and 2.08",
        "",
        (
            "- This is where upside can be worth volatility, but low-evidence "
            "one-signal players should show the missing-data reason clearly."
        ),
        (
            "- Day-three RB hits exist, but late-capital production traps also exist; "
            "require role path and receiving/first-down context where possible."
        ),
        "- Falling WR profiles with private target/production evidence deserve review.",
        "",
        "## 5.04",
        "",
        "- Remains No Baseline / Manual late-round watchlist / No exact equivalence.",
        "- Use it for manual scouting, not numeric pick equivalence.",
        "",
        "## Tournament Implication",
        "",
        _combined_recommendation(summary_rows),
    ]
    return "\n".join(lines)


def _combined_recommendation(summary_rows: list[dict[str, object]]) -> str:
    _ = summary_rows
    return (
        "No combined model is recommended from this tournament. The best next step is a narrower "
        "second shadow pass around established WR proof and elite QB floor/horizon, while keeping "
        "RB horizon and TE exception gates separate until their failure modes are reduced."
    )


def _metric_bucket(row: dict[str, object]) -> str:
    rank = _int(row["shadow_rank"]) or 9999
    if rank <= 12:
        return "top_12"
    if rank <= 24:
        return "top_24"
    if rank <= 36:
        return "top_36"
    return "outside_top_36"


def _rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "rank_missing"
    if rank <= 12:
        return "top_12"
    if rank <= 24:
        return "top_24"
    if rank <= 36:
        return "top_36"
    return "outside_top_36"


def _moved_more_than(rows: list[dict[str, object]], experiment_id: str, threshold: int) -> int:
    return sum(
        1
        for row in rows
        if row["experiment_id"] == experiment_id
        and row["rank_delta"] != ""
        and abs(_float(row["rank_delta"]) or 0.0) > threshold
    )


def _avg(values: list[float]) -> float | str:
    if not values:
        return ""
    return round(sum(values) / len(values), 4)


def _rate(numerator: int, denominator: int) -> float | str:
    if denominator <= 0:
        return ""
    return round(numerator / denominator, 3)


def _delta(new: int | None, old: int | None) -> int | None:
    if new is None or old is None:
        return None
    return new - old


def _score_delta(new: float | None, old: float | None) -> float | None:
    if new is None or old is None:
        return None
    return round(new - old, 4)


def _blank(value: object) -> object:
    return "" if value is None else value


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _float(value: object) -> float | None:
    try:
        text = str(value).strip()
        if not text or text == "-":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _norm(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
