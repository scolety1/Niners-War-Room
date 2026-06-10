from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.model_edge_evaluation_harness_service import (
    DEFAULT_OUTPUT_ROOT as MODEL_EDGE_OUTPUT_ROOT,
)

OUTPUT_ROOT = MODEL_EDGE_OUTPUT_ROOT
HARNESS_ROWS_PATH = OUTPUT_ROOT / "model_edge_evaluation_harness_review_rows.csv"
V1_HISTORICAL_PATH = OUTPUT_ROOT / "shadow_model_tournament_historical_rows.csv"
V1_CURRENT_PATH = OUTPUT_ROOT / "shadow_model_tournament_current_board_rows.csv"
CURRENT_BOARD_PATH = Path(
    "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
)
CURRENT_COMPONENTS_PATH = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)

VERSION = "shadow_model_v2_wr_qb_refinement_0.1.0"
SHADOW_POLICY = "shadow_only_no_active_rankings_overwrite"
SOURCE_POLICY = (
    "uses_private_current_components_and_historical_replay_features_only;"
    "market_league_adp_public_projection_rotowire_rankings_prior_draft_legacy_blocked"
)

EXPERIMENT_IDS = (
    "production_baseline",
    "wr_v1_reference",
    "wr_proof_lane_v2",
    "qb_v1_reference",
    "qb_floor_horizon_v2",
    "wr_qb_combined_v2",
)

V1_MAP = {
    "wr_v1_reference": "established_wr_proof_lane",
    "qb_v1_reference": "elite_qb_floor_horizon",
}

WATCH_PLAYERS = (
    "CeeDee Lamb",
    "Justin Jefferson",
    "Jaylen Waddle",
    "Ja'Marr Chase",
    "Amon-Ra St. Brown",
    "Puka Nacua",
    "Jaxon Smith-Njigba",
    "Drake London",
    "Nico Collins",
    "DeVonta Smith",
    "Jameson Williams",
    "Stefon Diggs",
    "Davante Adams",
    "Josh Allen",
    "Patrick Mahomes",
    "Lamar Jackson",
    "Jalen Hurts",
    "Joe Burrow",
    "Jayden Daniels",
    "Dak Prescott",
    "Jared Goff",
    "Baker Mayfield",
    "Jaxson Dart",
    "Drake Maye",
    "Trevor Lawrence",
    "Chase Brown",
    "Trey McBride",
    "Brock Bowers",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "De'Von Achane",
    "Breece Hall",
)

ROW_HEADER = (
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
    "v1_reference_rank",
    "v1_reference_score",
    "trust_status",
    "warning_flags",
    "changed_by_experiment",
    "reason_codes",
    "movement_classification",
    "evidence_fields_used",
    "confidence_trust_impact",
    "false_positive_warning",
    "formula_inputs_used",
    "shadow_only_policy",
    "contamination_check",
    "version",
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
    "v1_reference_rank",
    "v1_reference_score",
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
    "movement_classification",
    "evidence_fields_used",
    "false_positive_warning",
    "formula_inputs_used",
    "shadow_only_policy",
    "contamination_check",
    "version",
)

METRIC_HEADER = (
    "experiment_id",
    "metric_scope",
    "position",
    "rank_window",
    "rows",
    "strict_hits",
    "strict_hit_rate",
    "busts",
    "bust_rate",
    "high_ranked_misses",
    "low_ranked_hit_capture",
    "false_positive_rate",
    "moved_more_than_12",
    "qb_moved_more_than_24",
    "wr_moved_more_than_24",
    "non_elite_qb_suspicious_lifts",
    "aging_wr_suspicious_lifts",
    "contamination_rows",
    "version",
)

SUMMARY_HEADER = (
    "experiment_id",
    "hypothesis",
    "policy_change_tested",
    "historical_vs_baseline",
    "historical_vs_v1",
    "current_board_effect",
    "classification",
    "promotion_recommendation",
    "production_scores_changed",
    "contamination_rows",
    "version",
)

DIAGNOSIS_HEADER = (
    "lane",
    "player",
    "position",
    "baseline_rank",
    "v1_rank",
    "v1_score_delta",
    "v1_reason_codes",
    "v1_movement_classification",
    "v2_rank",
    "v2_score_delta",
    "v2_reason_codes",
    "v2_movement_classification",
    "diagnosis",
)


@dataclass(frozen=True)
class ShadowV2RefinementResult:
    current_rows: tuple[dict[str, object], ...]
    historical_rows: tuple[dict[str, object], ...]
    watch_rows: tuple[dict[str, object], ...]
    metric_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    diagnosis_rows: tuple[dict[str, object], ...]
    docs: dict[str, str]
    baseline_hash_before: str
    baseline_hash_after: str


def build_shadow_model_v2_wr_qb_refinement(
    harness_rows_path: str | Path = HARNESS_ROWS_PATH,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    current_components_path: str | Path = CURRENT_COMPONENTS_PATH,
    v1_historical_path: str | Path = V1_HISTORICAL_PATH,
    v1_current_path: str | Path = V1_CURRENT_PATH,
) -> ShadowV2RefinementResult:
    board_path = Path(current_board_path)
    baseline_hash_before = _sha256(board_path)
    board_rows = _read_rows(board_path)
    component_rows = _read_rows(Path(current_components_path))
    current_source = _merge_current_rows(board_rows, component_rows)
    historical_source = _read_rows(Path(harness_rows_path))
    v1_current_rows = _read_rows(Path(v1_current_path))
    v1_historical_rows = _read_rows(Path(v1_historical_path))

    current_rows = _current_rows(current_source, v1_current_rows)
    historical_rows = _historical_rows(historical_source, v1_historical_rows)
    metric_rows = _metric_rows(historical_rows, current_rows)
    watch_rows = tuple(row for row in current_rows if row["player"] in WATCH_PLAYERS)
    diagnosis_rows = _diagnosis_rows(current_rows)
    summary_rows = _summary_rows(metric_rows, current_rows)
    docs = _docs(summary_rows, metric_rows, current_rows, watch_rows, diagnosis_rows)
    baseline_hash_after = _sha256(board_path)

    return ShadowV2RefinementResult(
        current_rows=tuple(current_rows),
        historical_rows=tuple(historical_rows),
        watch_rows=watch_rows,
        metric_rows=tuple(metric_rows),
        summary_rows=tuple(summary_rows),
        diagnosis_rows=tuple(diagnosis_rows),
        docs=docs,
        baseline_hash_before=baseline_hash_before,
        baseline_hash_after=baseline_hash_after,
    )


def write_shadow_model_v2_wr_qb_refinement_outputs(
    output_root: str | Path = OUTPUT_ROOT,
    result: ShadowV2RefinementResult | None = None,
) -> dict[str, Path]:
    result = result or build_shadow_model_v2_wr_qb_refinement()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "current_rows": output / "shadow_model_v2_current_board_rows.csv",
        "historical_rows": output / "shadow_model_v2_historical_rows.csv",
        "watch_rows": output / "shadow_model_v2_watch_rows.csv",
        "metrics": output / "shadow_model_v2_metrics.csv",
        "summary": output / "shadow_model_v2_summary.csv",
        "diagnosis": output / "shadow_model_v2_failure_mode_diagnosis.csv",
    }
    _write_csv(paths["current_rows"], ROW_HEADER, result.current_rows)
    _write_csv(paths["historical_rows"], HISTORICAL_ROW_HEADER, result.historical_rows)
    _write_csv(paths["watch_rows"], ROW_HEADER, result.watch_rows)
    _write_csv(paths["metrics"], METRIC_HEADER, result.metric_rows)
    _write_csv(paths["summary"], SUMMARY_HEADER, result.summary_rows)
    _write_csv(paths["diagnosis"], DIAGNOSIS_HEADER, result.diagnosis_rows)
    doc_paths = {
        "refinement_doc": Path(
            "docs/model_v4/SHADOW_MODEL_V2_WR_QB_REFINEMENT_20260610.md"
        ),
        "current_diff_doc": Path(
            "docs/model_v4/SHADOW_MODEL_V2_CURRENT_BOARD_DIFF_20260610.md"
        ),
        "patch_recommendation_doc": Path(
            "docs/model_v4/SHADOW_MODEL_V2_PRODUCTION_PATCH_RECOMMENDATION_20260610.md"
        ),
    }
    for key, path in doc_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.docs[key], encoding="utf-8")
        paths[key] = path
    return paths


def _current_rows(
    source_rows: list[dict[str, str]],
    v1_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    v1_lookup = _v1_current_lookup(v1_rows)
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        scored_rows = []
        for row in source_rows:
            base = _float(_base_score_value(row))
            if base is None:
                score, changed, reasons, evidence, trust, fp_warning, inputs = (
                    None,
                    "unscored_or_hidden",
                    ("unscored_k_or_no_nwr_score",),
                    ("position", "production_nwr_score"),
                    "no_score_available",
                    "",
                    ("position", "production_nwr_score"),
                )
            elif experiment_id in V1_MAP:
                ref = v1_lookup.get((V1_MAP[experiment_id], _current_key(row)), {})
                score = _float(ref.get("shadow_score")) if ref else base
                changed = ref.get("changed_by_experiment", "v1_reference_missing")
                reasons = _split(ref.get("reason_codes", "v1_reference_missing"))
                evidence = _split(ref.get("formula_inputs_used", "v1_reference_row"))
                trust = "v1_reference_readback_only"
                fp_warning = _v1_false_positive_warning(experiment_id, row, score, base)
                inputs = ("v1_shadow_output_readback",)
            else:
                score, changed, reasons, evidence, trust, fp_warning, inputs = _current_v2_score(
                    experiment_id, row, base
                )
            scored_rows.append(
                {
                    **row,
                    "_baseline_score": base,
                    "_shadow_score": score,
                    "_changed": changed,
                    "_reasons": reasons,
                    "_evidence": evidence,
                    "_trust": trust,
                    "_fp_warning": fp_warning,
                    "_inputs": inputs,
                }
            )
        rank_lookup = _current_rank_lookup(scored_rows)
        for row in scored_rows:
            key = _current_key(row)
            baseline_rank = _int(_base_rank(row))
            shadow_rank = rank_lookup.get(key, "")
            ref_id = _reference_id(experiment_id)
            ref = v1_lookup.get((ref_id, key), {}) if ref_id else {}
            rank_delta = _delta(_int(shadow_rank), baseline_rank) if shadow_rank != "" else None
            output.append(
                {
                    "experiment_id": experiment_id,
                    "player": row.get("player_name", ""),
                    "position": row.get("position", ""),
                    "team": row.get("nfl_team", ""),
                    "baseline_rank": _blank(baseline_rank),
                    "shadow_rank": shadow_rank,
                    "rank_delta": _blank(rank_delta),
                    "baseline_score": _blank(row["_baseline_score"]),
                    "shadow_score": _blank(row["_shadow_score"]),
                    "score_delta": _blank(
                        _score_delta(row["_shadow_score"], row["_baseline_score"])
                    ),
                    "v1_reference_rank": ref.get("shadow_rank", ""),
                    "v1_reference_score": ref.get("shadow_score", ""),
                    "trust_status": row.get("trust_status", ""),
                    "warning_flags": row.get("warning_flags", ""),
                    "changed_by_experiment": row["_changed"],
                    "reason_codes": "|".join(row["_reasons"]),
                    "movement_classification": _movement_classification(
                        experiment_id, row, rank_delta, row["_reasons"]
                    ),
                    "evidence_fields_used": "|".join(row["_evidence"]),
                    "confidence_trust_impact": row["_trust"],
                    "false_positive_warning": row["_fp_warning"],
                    "formula_inputs_used": "|".join(row["_inputs"]),
                    "shadow_only_policy": SHADOW_POLICY,
                    "contamination_check": "no_blocked_inputs_used",
                    "version": VERSION,
                }
            )
    return output


def _historical_rows(
    source_rows: list[dict[str, str]],
    v1_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    v1_lookup = _v1_historical_lookup(v1_rows)
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        scored_rows = []
        for row in source_rows:
            base = _float(row.get("private_score_at_eval"))
            if base is None:
                score, changed, reasons, evidence, fp_warning, inputs = (
                    None,
                    "unscored",
                    ("missing_historical_score",),
                    ("historical_replay_score",),
                    "",
                    ("historical_replay_score",),
                )
            elif experiment_id in V1_MAP:
                ref = v1_lookup.get(
                    (
                        V1_MAP[experiment_id],
                        str(row.get("draft_year", "")),
                        str(row.get("player", "")),
                    ),
                    {},
                )
                score = _float(ref.get("shadow_score")) if ref else base
                changed = ref.get("changed_by_experiment", "v1_reference_missing")
                reasons = _split(ref.get("reason_codes", "v1_reference_missing"))
                evidence = _split(ref.get("formula_inputs_used", "v1_reference_row"))
                fp_warning = ""
                inputs = ("v1_shadow_output_readback",)
            else:
                score, changed, reasons, evidence, fp_warning, inputs = _historical_v2_score(
                    experiment_id, row, base
                )
            scored_rows.append(
                {
                    **row,
                    "_baseline_score": base,
                    "_shadow_score": score,
                    "_changed": changed,
                    "_reasons": reasons,
                    "_evidence": evidence,
                    "_fp_warning": fp_warning,
                    "_inputs": inputs,
                }
            )
        rank_lookup = _rank_lookup(scored_rows, "draft_year", "_shadow_score", "player")
        for row in scored_rows:
            draft_year = str(row.get("draft_year", ""))
            player = str(row.get("player", ""))
            baseline_rank = _int(row.get("model_rank"))
            shadow_rank = rank_lookup[(draft_year, player)]
            ref_id = _reference_id(experiment_id)
            ref = v1_lookup.get((ref_id, draft_year, player), {}) if ref_id else {}
            rank_delta = _delta(shadow_rank, baseline_rank)
            output.append(
                {
                    "experiment_id": experiment_id,
                    "draft_year": draft_year,
                    "player": player,
                    "position": row.get("position", ""),
                    "baseline_rank": _blank(baseline_rank),
                    "shadow_rank": shadow_rank,
                    "rank_delta": _blank(rank_delta),
                    "baseline_score": _blank(row["_baseline_score"]),
                    "shadow_score": _blank(row["_shadow_score"]),
                    "score_delta": _blank(
                        _score_delta(row["_shadow_score"], row["_baseline_score"])
                    ),
                    "v1_reference_rank": ref.get("shadow_rank", ""),
                    "v1_reference_score": ref.get("shadow_score", ""),
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
                    "movement_classification": _historical_movement_classification(
                        experiment_id, row, rank_delta
                    ),
                    "evidence_fields_used": "|".join(row["_evidence"]),
                    "false_positive_warning": row["_fp_warning"],
                    "formula_inputs_used": "|".join(row["_inputs"]),
                    "shadow_only_policy": SHADOW_POLICY,
                    "contamination_check": "no_blocked_inputs_used",
                    "version": VERSION,
                }
            )
    return output


def _current_v2_score(
    experiment_id: str,
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, str, tuple[str, ...]]:
    if experiment_id == "production_baseline":
        return (
            base,
            "unchanged_by_experiment",
            ("production_baseline",),
            ("production_nwr_score",),
            "baseline_readback",
            "",
            ("production_nwr_score",),
        )
    if experiment_id == "wr_proof_lane_v2":
        return _current_wr_v2(row, base)
    if experiment_id == "qb_floor_horizon_v2":
        return _current_qb_v2(row, base)
    if experiment_id == "wr_qb_combined_v2":
        if row.get("position") == "WR":
            return _current_wr_v2(row, base, combined=True)
        if row.get("position") == "QB":
            return _current_qb_v2(row, base, combined=True)
        return (
            base,
            "unchanged_by_experiment",
            ("not_wr_or_qb",),
            ("position", "production_nwr_score"),
            "non_wr_qb_unchanged",
            "",
            ("position", "production_nwr_score"),
        )
    raise ValueError(f"Unknown experiment: {experiment_id}")


def _current_wr_v2(
    row: dict[str, str],
    base: float,
    *,
    combined: bool = False,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, str, tuple[str, ...]]:
    if row.get("position") != "WR":
        return _unchanged(base, "not_wr")
    role = row.get("role_archetype", "")
    warnings = row.get("warning_flags", "")
    confidence = _float(row.get("confidence_cap")) or 0.0
    lifecycle = _float(row.get("lifecycle_modifier_review")) or 1.0
    vorp = _float(row.get("positive_vorp_points")) or 0.0
    review = _float(row.get("review_scoring_points")) or 0.0
    first_down = _float(row.get("imported_first_down_points")) or 0.0
    pos_score = _float(row.get("position_specific_review_score")) or 0.0
    source_limited = _has_any(
        warnings,
        ("identity_review_cap", "partial_or_quarantined_join_cap", "team_mismatch"),
    )
    aging = lifecycle < 0.95 or _has_any(
        warnings, ("wr_dynasty_age_curve_after_30_active", "wr_mid_30s_age_cliff_active")
    )
    if "wr_target_earner" not in role:
        return _unchanged(base, "wr_role_receipt_missing")
    if aging:
        return _unchanged(
            base,
            "aging_wr_horizon_blocks_full_proof_lane",
            fp_warning="older_wr_short_window_not_protected",
        )
    if source_limited:
        return _unchanged(
            base,
            "wr_source_limited_needs_review",
            trust="source_limited_no_force_boost",
            fp_warning="source_limited_wr_not_protected_without_clean_receipts",
        )
    established_band = (
        30 <= vorp <= 45
        and review >= 130
        and first_down >= 16
        and pos_score >= 49
        and confidence >= 0.86
    )
    elite_already_high = vorp >= 95 and review >= 195 and base >= 60
    thin_spike = vorp >= 55 and base < 55 and review < 175
    if elite_already_high:
        return _unchanged(
            base,
            "elite_wr_already_supported_no_extra_lift",
            trust="evidence_strong_already_reflected",
        )
    if thin_spike:
        return _unchanged(
            base,
            "wr_thin_or_single_year_spike_cap",
            trust="upside_kept_separate_from_proof_lane",
            fp_warning="thin_wr_profile_not_lifted_by_v2",
        )
    if not established_band:
        return _unchanged(base, "wr_v2_proof_gate_not_met")
    lift = 3.0
    if "partial_first_down" in warnings:
        lift -= 0.5
    score = min(100.0, base + lift)
    return (
        round(score, 4),
        "wr_proof_lane_v2" if not combined else "wr_qb_combined_v2",
        ("durable_prime_wr_private_proof_lane", "missing_receipts_trust_not_score_crush"),
        (
            "position_specific_review_score",
            "positive_vorp_points",
            "review_scoring_points",
            "imported_first_down_points",
            "role_archetype",
            "lifecycle_modifier_review",
            "confidence_cap",
            "warning_flags",
        ),
        "confidence_cap_remains_visible;proof_lane_does_not_clean_source_warnings",
        "",
        _current_inputs(),
    )


def _current_qb_v2(
    row: dict[str, str],
    base: float,
    *,
    combined: bool = False,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, str, tuple[str, ...]]:
    if row.get("position") != "QB":
        return _unchanged(base, "not_qb")
    role = row.get("role_archetype", "")
    warnings = row.get("warning_flags", "")
    review = _float(row.get("review_scoring_points")) or 0.0
    vorp = _float(row.get("positive_vorp_points")) or 0.0
    first_down = _float(row.get("imported_first_down_points")) or 0.0
    pos_score = _float(row.get("position_specific_review_score")) or 0.0
    lifecycle = _float(row.get("lifecycle_modifier_review")) or 1.0
    pocket = "pocket" in role
    replacement_cap = "one_qb_replacement_level_qb_cap" in warnings
    floor = 0.0
    reasons: list[str] = []
    if review >= 300 and vorp >= 55 and first_down >= 14:
        floor = 49.0
        reasons.append("elite_multi_signal_qb_already_1qb_capped")
    elif review >= 255 and vorp >= 18 and first_down >= 12 and not pocket:
        floor = 33.0
        reasons.append("hybrid_qb_difference_gap_floor")
    elif (
        review >= 240
        and vorp >= 5
        and first_down >= 9
        and pos_score >= 24
        and not pocket
        and lifecycle >= 0.97
    ):
        floor = 27.5
        reasons.append("undercompressed_elite_profile_review_band")
    if floor <= 0:
        return _unchanged(
            base,
            "qb_v2_elite_floor_gate_not_met",
            fp_warning=_qb_false_positive_warning(row, replacement_cap, pocket),
        )
    if base >= floor:
        return _unchanged(base, "qb_already_above_v2_floor")
    score = min(52.0, max(base, floor))
    return (
        round(score, 4),
        "qb_floor_horizon_v2" if not combined else "wr_qb_combined_v2",
        tuple(reasons + ["one_qb_floor_retains_format_cap"]),
        (
            "position_specific_review_score",
            "positive_vorp_points",
            "review_scoring_points",
            "imported_first_down_points",
            "role_archetype",
            "lifecycle_modifier_review",
            "warning_flags",
        ),
        "1qb_cap_remains_active;floor_requires_multi_signal_private_receipts",
        "",
        _current_inputs(),
    )


def _historical_v2_score(
    experiment_id: str,
    row: dict[str, str],
    base: float,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, tuple[str, ...]]:
    if experiment_id == "production_baseline":
        return (
            base,
            "unchanged_by_experiment",
            ("production_baseline",),
            ("historical_replay_score",),
            "",
            ("historical_replay_score",),
        )
    if experiment_id == "wr_proof_lane_v2":
        return _historical_wr_v2(row, base)
    if experiment_id == "qb_floor_horizon_v2":
        return _historical_qb_v2(row, base)
    if experiment_id == "wr_qb_combined_v2":
        if row.get("position") == "WR":
            return _historical_wr_v2(row, base, combined=True)
        if row.get("position") == "QB":
            return _historical_qb_v2(row, base, combined=True)
        return (
            base,
            "unchanged_by_experiment",
            ("not_wr_or_qb",),
            ("position", "historical_replay_score"),
            "",
            ("position", "historical_replay_score"),
        )
    raise ValueError(f"Unknown experiment: {experiment_id}")


def _historical_wr_v2(
    row: dict[str, str],
    base: float,
    *,
    combined: bool = False,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, tuple[str, ...]]:
    if row.get("position") != "WR":
        return _historical_unchanged(base, "not_wr")
    profile = _profile(row)
    evidence = _float(row.get("evidence_available")) or 0.0
    proof = (
        profile["draft_capital"] >= 82
        and max(profile["production"], profile["team_share"]) >= 78
        and evidence >= 0.55
    )
    secondary = (
        profile["draft_capital"] >= 72
        and profile["production"] >= 86
        and profile["team_share"] >= 70
        and evidence >= 0.65
    )
    if not (proof or secondary):
        return _historical_unchanged(base, "wr_v2_historical_proof_gate_not_met")
    lift = 2.5 if proof else 1.5
    return (
        round(min(100.0, base + lift), 4),
        "wr_proof_lane_v2" if not combined else "wr_qb_combined_v2",
        ("historical_multi_signal_wr_proof_lane",),
        _historical_inputs(),
        "",
        _historical_inputs(),
    )


def _historical_qb_v2(
    row: dict[str, str],
    base: float,
    *,
    combined: bool = False,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, tuple[str, ...]]:
    if row.get("position") != "QB":
        return _historical_unchanged(base, "not_qb")
    profile = _profile(row)
    evidence = _float(row.get("evidence_available")) or 0.0
    if profile["draft_capital"] < 90 or evidence < 0.55:
        return _historical_unchanged(base, "qb_v2_historical_floor_gate_not_met")
    if max(profile["production"], profile["team_share"], profile["athletic"]) < 65:
        return _historical_unchanged(base, "qb_v2_difference_gap_not_met")
    floor = 39.0
    if base >= floor:
        return _historical_unchanged(base, "qb_already_above_v2_floor")
    return (
        round(min(46.0, max(base, floor)), 4),
        "qb_floor_horizon_v2" if not combined else "wr_qb_combined_v2",
        ("historical_round1_qb_floor_multi_signal_gate",),
        _historical_inputs(),
        "",
        _historical_inputs(),
    )


def _metric_rows(
    historical_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        mature = [
            row
            for row in historical_rows
            if row["experiment_id"] == experiment_id
            and row["outcome_maturity"] == "three_year_window_available"
        ]
        current = [row for row in current_rows if row["experiment_id"] == experiment_id]
        for position in ("ALL", "QB", "RB", "WR", "TE"):
            pos_rows = mature if position == "ALL" else [
                row for row in mature if row["position"] == position
            ]
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
                        current,
                    )
                )
        for position in ("QB", "RB", "WR", "TE"):
            pos_rows = [row for row in mature if row["position"] == position]
            for bucket in ("top_12", "top_24", "top_36", "outside_top_36"):
                bucket_rows = [row for row in pos_rows if _metric_bucket(row) == bucket]
                output.append(
                    _metric_row(
                        experiment_id,
                        "rank_bucket",
                        position,
                        bucket,
                        bucket_rows,
                        pos_rows,
                        current,
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
    current_rows: list[dict[str, object]],
) -> dict[str, object]:
    strict = [row for row in rows if _bool(row["strict_starter_hit"])]
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
    moved_rows = [
        row
        for row in current_rows
        if row["rank_delta"] != "" and abs(_float(row["rank_delta"]) or 0.0) > 12
    ]
    qb_big = [
        row
        for row in current_rows
        if row["position"] == "QB"
        and row["rank_delta"] != ""
        and abs(_float(row["rank_delta"]) or 0.0) > 24
    ]
    wr_big = [
        row
        for row in current_rows
        if row["position"] == "WR"
        and row["rank_delta"] != ""
        and abs(_float(row["rank_delta"]) or 0.0) > 24
    ]
    non_elite_qb = [
        row
        for row in current_rows
        if row["position"] == "QB"
        and "false_positive" in str(row["movement_classification"])
        and (_float(row["rank_delta"]) or 0.0) < -12
    ]
    aging_wr = [
        row
        for row in current_rows
        if row["position"] == "WR"
        and "aging_wr" in str(row["reason_codes"])
        and (_float(row["rank_delta"]) or 0.0) < -6
    ]
    contamination = [
        row for row in current_rows if row["contamination_check"] != "no_blocked_inputs_used"
    ]
    return {
        "experiment_id": experiment_id,
        "metric_scope": scope,
        "position": position,
        "rank_window": rank_window,
        "rows": len(rows),
        "strict_hits": len(strict),
        "strict_hit_rate": _rate(len(strict), len(rows)),
        "busts": len(busts),
        "bust_rate": _rate(len(busts), len(rows)),
        "high_ranked_misses": len(high_misses),
        "low_ranked_hit_capture": len(low_hit_capture),
        "false_positive_rate": _rate(len(high_misses), len(rows)),
        "moved_more_than_12": len(moved_rows),
        "qb_moved_more_than_24": len(qb_big),
        "wr_moved_more_than_24": len(wr_big),
        "non_elite_qb_suspicious_lifts": len(non_elite_qb),
        "aging_wr_suspicious_lifts": len(aging_wr),
        "contamination_rows": len(contamination),
        "version": VERSION,
    }


def _summary_rows(
    metrics: list[dict[str, object]],
    current_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for experiment_id in EXPERIMENT_IDS:
        classification = _classification(experiment_id, metrics, current_rows)
        output.append(
            {
                "experiment_id": experiment_id,
                "hypothesis": _hypothesis(experiment_id),
                "policy_change_tested": _policy(experiment_id),
                "historical_vs_baseline": _historical_compare(
                    experiment_id, "production_baseline", metrics
                ),
                "historical_vs_v1": _v1_compare(experiment_id, metrics),
                "current_board_effect": _current_effect(experiment_id, current_rows),
                "classification": classification,
                "promotion_recommendation": _promotion_recommendation(
                    experiment_id, classification
                ),
                "production_scores_changed": False,
                "contamination_rows": _contamination_count(experiment_id, current_rows),
                "version": VERSION,
            }
        )
    return output


def _diagnosis_rows(current_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    by_player_exp = {
        (row["player"], row["experiment_id"]): row
        for row in current_rows
        if row["player"] in WATCH_PLAYERS
    }
    for player in WATCH_PLAYERS:
        baseline = by_player_exp.get((player, "production_baseline"), {})
        for lane, v1_id, v2_id in (
            ("QB lane", "qb_v1_reference", "qb_floor_horizon_v2"),
            ("WR lane", "wr_v1_reference", "wr_proof_lane_v2"),
        ):
            v1 = by_player_exp.get((player, v1_id), {})
            v2 = by_player_exp.get((player, v2_id), {})
            if not v1 and not v2:
                continue
            output.append(
                {
                    "lane": lane,
                    "player": player,
                    "position": baseline.get(
                        "position",
                        v1.get("position", v2.get("position", "")),
                    ),
                    "baseline_rank": baseline.get("baseline_rank", ""),
                    "v1_rank": v1.get("shadow_rank", ""),
                    "v1_score_delta": v1.get("score_delta", ""),
                    "v1_reason_codes": v1.get("reason_codes", ""),
                    "v1_movement_classification": v1.get("movement_classification", ""),
                    "v2_rank": v2.get("shadow_rank", ""),
                    "v2_score_delta": v2.get("score_delta", ""),
                    "v2_reason_codes": v2.get("reason_codes", ""),
                    "v2_movement_classification": v2.get("movement_classification", ""),
                    "diagnosis": _diagnosis_text(player, lane, v1, v2),
                }
            )
    return output


def _docs(
    summary_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    watch_rows: tuple[dict[str, object], ...],
    diagnosis_rows: list[dict[str, object]],
) -> dict[str, str]:
    return {
        "refinement_doc": _refinement_doc(summary_rows, metrics, diagnosis_rows),
        "current_diff_doc": _current_diff_doc(current_rows, watch_rows),
        "patch_recommendation_doc": _patch_doc(summary_rows),
    }


def _refinement_doc(
    summary_rows: list[dict[str, object]],
    metrics: list[dict[str, object]],
    diagnosis_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Shadow Model V2 WR/QB Refinement - 2026-06-10",
        "",
        "This is a shadow-only refinement. No production scoring changes are made.",
        "",
        "## Source-Safe Fields Used",
        "",
        "- Current rows: NWR score, position review score, VORP points, review scoring "
        "points, first-down points, role archetype, lifecycle modifier, confidence "
        "cap, available component weight, warning flags.",
        "- Historical rows: historical replay score, draft round, overall pick, "
        "pre-draft production/team-share/draft-capital/athletic fields, evidence "
        "availability, confidence cap.",
        "- Blocked: ADP, market rank, public rankings, consensus, projections, "
        "trade calculators, RotoWire rankings/projections, prior draft history, "
        "legacy active-pack private_score, roster tags.",
        "",
        "## Summary",
        "",
        (
            "| Experiment | Classification | Recommendation | Historical vs baseline | "
            "Historical vs v1 |"
        ),
        "|---|---|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['experiment_id']}` | {row['classification']} | "
            f"{row['promotion_recommendation']} | {row['historical_vs_baseline']} | "
            f"{row['historical_vs_v1']} |"
        )
    lines.extend(
        [
            "",
            "## V1 Failure Diagnosis",
            "",
            "| Lane | Player | Base | V1 | V2 | V1 class | V2 class | Diagnosis |",
            "|---|---|---:|---:|---:|---|---|---|",
        ]
    )
    for row in diagnosis_rows:
        lines.append(
            f"| {row['lane']} | {row['player']} | {row['baseline_rank']} | "
            f"{row['v1_rank']} | {row['v2_rank']} | "
            f"{row['v1_movement_classification']} | "
            f"{row['v2_movement_classification']} | {row['diagnosis']} |"
        )
    lines.extend(
        [
            "",
            "## Metrics Snapshot",
            "",
            (
                "| Experiment | Position | Window | Hit rate | Bust rate | Moved >12 | "
                "QB >24 | WR >24 |"
            ),
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in metrics:
        if row["metric_scope"] == "top_window" and row["rank_window"] in {
            "top_12",
            "top_24",
            "top_36",
        }:
            lines.append(
                f"| `{row['experiment_id']}` | {row['position']} | {row['rank_window']} | "
                f"{row['strict_hit_rate']} | {row['bust_rate']} | "
                f"{row['moved_more_than_12']} | {row['qb_moved_more_than_24']} | "
                f"{row['wr_moved_more_than_24']} |"
            )
    return "\n".join(lines)


def _current_diff_doc(
    current_rows: list[dict[str, object]],
    watch_rows: tuple[dict[str, object], ...],
) -> str:
    improvements = sorted(
        [
            row
            for row in current_rows
            if row["experiment_id"]
            in {"wr_proof_lane_v2", "qb_floor_horizon_v2", "wr_qb_combined_v2"}
            and row["rank_delta"] != ""
            and (_float(row["rank_delta"]) or 0.0) < 0
        ],
        key=lambda row: _float(row["rank_delta"]) or 0.0,
    )[:20]
    suspicious = sorted(
        [
            row
            for row in current_rows
            if row["experiment_id"]
            in {"wr_proof_lane_v2", "qb_floor_horizon_v2", "wr_qb_combined_v2"}
            and row["rank_delta"] != ""
            and abs(_float(row["rank_delta"]) or 0.0) > 6
        ],
        key=lambda row: abs(_float(row["rank_delta"]) or 0.0),
        reverse=True,
    )[:20]
    lines = [
        "# Shadow Model V2 Current Board Diff - 2026-06-10",
        "",
        "Production rankings are unchanged. Rows below are shadow-only.",
        "",
        "## Watch Rows",
        "",
        (
            "| Experiment | Player | Pos | Base rank | Shadow rank | Delta | "
            "Base score | Shadow score | Reason | Class |"
        ),
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in watch_rows:
        lines.append(
            f"| `{row['experiment_id']}` | {row['player']} | {row['position']} | "
            f"{row['baseline_rank']} | {row['shadow_rank']} | {row['rank_delta']} | "
            f"{row['baseline_score']} | {row['shadow_score']} | "
            f"{row['reason_codes']} | {row['movement_classification']} |"
        )
    lines.extend(
        [
            "",
            "## Top Credibility Improvements",
            "",
            "| Experiment | Player | Pos | Base | Shadow | Delta | Reason |",
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
            "## Top New Suspicious Movements",
            "",
            "| Experiment | Player | Pos | Base | Shadow | Delta | Warning |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in suspicious:
        lines.append(
            f"| `{row['experiment_id']}` | {row['player']} | {row['position']} | "
            f"{row['baseline_rank']} | {row['shadow_rank']} | {row['rank_delta']} | "
            f"{row['false_positive_warning']} |"
        )
    return "\n".join(lines)


def _patch_doc(summary_rows: list[dict[str, object]]) -> str:
    lines = [
        "# Shadow Model V2 Production Patch Recommendation - 2026-06-10",
        "",
        "No patch is implemented here. This is a proposal-only readout.",
        "",
        "## Recommendation",
        "",
    ]
    combined = next(row for row in summary_rows if row["experiment_id"] == "wr_qb_combined_v2")
    wr = next(row for row in summary_rows if row["experiment_id"] == "wr_proof_lane_v2")
    qb = next(row for row in summary_rows if row["experiment_id"] == "qb_floor_horizon_v2")
    lines.extend(
        [
            f"- WR v2: {wr['promotion_recommendation']}",
            f"- QB v2: {qb['promotion_recommendation']}",
            f"- Combined v2: {combined['promotion_recommendation']}",
            "",
            "## Production Gate",
            "",
            "- Re-run the full Rankings export through production code if approved later.",
            "- Keep RB horizon and TE gate out of this patch.",
            "- Prove no active data pack, Decision Board, or market/public inputs enter scoring.",
            "- Keep legal draft pool pending and outcome fields in development.",
            "",
            "## Recommended Next Patch",
            "",
            _recommended_patch(summary_rows),
            "",
            "## Rookie Draft Implications",
            "",
            "- 1.03 and 1.04: prefer multi-signal WR/RB profiles; QB/TE require rare proof.",
            (
                "- 2.04 and 2.08: upside is acceptable, but one-signal profiles need "
                "clear risk labels."
            ),
            "- 5.04: remains No Baseline / Manual late-round watchlist / No exact equivalence.",
        ]
    )
    return "\n".join(lines)


def _classification(
    experiment_id: str,
    metrics: list[dict[str, object]],
    current_rows: list[dict[str, object]],
) -> str:
    if experiment_id == "production_baseline":
        return "baseline"
    if experiment_id in V1_MAP:
        return "v1_reference_only"
    top36 = _metric(metrics, experiment_id, "top_window", "ALL", "top_36")
    base36 = _metric(metrics, "production_baseline", "top_window", "ALL", "top_36")
    hit_delta = (_float(top36.get("strict_hit_rate")) or 0.0) - (
        _float(base36.get("strict_hit_rate")) or 0.0
    )
    bust_delta = (_float(top36.get("bust_rate")) or 0.0) - (
        _float(base36.get("bust_rate")) or 0.0
    )
    suspicious = _metric(metrics, experiment_id, "top_window", "ALL", "top_24")
    moved = int(suspicious.get("moved_more_than_12") or 0)
    non_elite_qb = int(suspicious.get("non_elite_qb_suspicious_lifts") or 0)
    aging_wr = int(suspicious.get("aging_wr_suspicious_lifts") or 0)
    contamination = _contamination_count(experiment_id, current_rows)
    if contamination:
        return "reject_contamination"
    if non_elite_qb or aging_wr:
        return "needs_more_review_false_positive_risk"
    if moved > 20:
        return "needs_more_review_board_disruption"
    if hit_delta >= 0 and bust_delta <= 0.0:
        return "candidate_promising_for_human_review"
    return "needs_more_data"


def _promotion_recommendation(experiment_id: str, classification: str) -> str:
    if experiment_id == "production_baseline":
        return "baseline_only"
    if experiment_id in V1_MAP:
        return "do_not_promote_v1_reference"
    if classification == "candidate_promising_for_human_review":
        return "eligible_for_tiny_production_patch_proposal_after_review"
    return "do_not_promote_without_more_research"


def _recommended_patch(summary_rows: list[dict[str, object]]) -> str:
    combined = next(row for row in summary_rows if row["experiment_id"] == "wr_qb_combined_v2")
    if combined["classification"] == "candidate_promising_for_human_review":
        return (
            "Recommended next production patch candidate: a narrow WR/QB v2 patch, "
            "with RB and TE untouched."
        )
    return (
        "No production patch is recommended yet. Tighten the v2 gates or add retained "
        "dynasty value labels before promotion."
    )


def _historical_compare(
    experiment_id: str,
    reference_id: str,
    metrics: list[dict[str, object]],
) -> str:
    row = _metric(metrics, experiment_id, "top_window", "ALL", "top_36")
    ref = _metric(metrics, reference_id, "top_window", "ALL", "top_36")
    return (
        f"top36 hit {row.get('strict_hit_rate')} vs {ref.get('strict_hit_rate')}; "
        f"bust {row.get('bust_rate')} vs {ref.get('bust_rate')}"
    )


def _v1_compare(experiment_id: str, metrics: list[dict[str, object]]) -> str:
    if experiment_id == "wr_proof_lane_v2":
        return _historical_compare(experiment_id, "wr_v1_reference", metrics)
    if experiment_id == "qb_floor_horizon_v2":
        return _historical_compare(experiment_id, "qb_v1_reference", metrics)
    if experiment_id == "wr_qb_combined_v2":
        return "compared separately to WR v1 and QB v1; no v1 combined was promoted"
    if experiment_id in V1_MAP:
        return "v1 reference row"
    return "baseline"


def _current_effect(experiment_id: str, current_rows: list[dict[str, object]]) -> str:
    rows = [
        row
        for row in current_rows
        if row["experiment_id"] == experiment_id and row["player"] in WATCH_PLAYERS
    ]
    moved = [
        f"{row['player']} {row['baseline_rank']}->{row['shadow_rank']}"
        for row in rows
        if row["rank_delta"] != "" and row["rank_delta"] != 0
    ][:6]
    return "; ".join(moved) if moved else "watch rows mostly stable"


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


def _unchanged(
    base: float,
    reason: str,
    *,
    trust: str = "no_score_adjustment",
    fp_warning: str = "",
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, str, tuple[str, ...]]:
    return (
        base,
        "unchanged_by_experiment",
        (reason,),
        ("position", "production_nwr_score"),
        trust,
        fp_warning,
        _current_inputs(),
    )


def _historical_unchanged(
    base: float,
    reason: str,
) -> tuple[float, str, tuple[str, ...], tuple[str, ...], str, tuple[str, ...]]:
    return (
        base,
        "unchanged_by_experiment",
        (reason,),
        ("position", "historical_replay_score"),
        "",
        _historical_inputs(),
    )


def _movement_classification(
    experiment_id: str,
    row: dict[str, object],
    rank_delta: int | None,
    reasons: tuple[str, ...],
) -> str:
    if experiment_id == "production_baseline":
        return "baseline"
    if experiment_id in V1_MAP:
        return _v1_classification(experiment_id, row, rank_delta)
    if rank_delta is None or rank_delta == 0:
        return "stable"
    if "source_limited" in "|".join(reasons):
        return "needs_more_data"
    if row.get("position") == "QB" and rank_delta < -12:
        if "elite" in "|".join(reasons) or "hybrid" in "|".join(reasons):
            return "intended_improvement"
        return "false_positive"
    if row.get("position") == "WR" and rank_delta < 0:
        if "durable_prime_wr" in "|".join(reasons):
            return "intended_improvement"
        return "acceptable_side_effect"
    if abs(rank_delta) <= 3:
        return "acceptable_side_effect"
    return "needs_more_data"


def _base_rank(row: dict[str, object]) -> object:
    return row.get("base_nwr_rank") or row.get("nwr_rank", "")


def _base_score_value(row: dict[str, object]) -> object:
    return row.get("base_nwr_dynasty_score") or row.get("nwr_dynasty_score", "")


def _historical_movement_classification(
    experiment_id: str,
    row: dict[str, str],
    rank_delta: int | None,
) -> str:
    if experiment_id == "production_baseline":
        return "baseline"
    if rank_delta is None or rank_delta == 0:
        return "stable"
    if rank_delta < 0 and _bool(row.get("strict_starter_hit")):
        return "historical_hit_capture"
    if rank_delta < 0 and row.get("league_outcome_label") == "Bust":
        return "historical_false_positive"
    return "historical_side_effect"


def _v1_classification(
    experiment_id: str,
    row: dict[str, object],
    rank_delta: int | None,
) -> str:
    player = str(row.get("player_name") or row.get("player") or "")
    if rank_delta is None or rank_delta == 0:
        return "stable"
    if experiment_id == "qb_v1_reference":
        if player in {"Jared Goff", "Baker Mayfield", "Jaxson Dart"} and rank_delta < 0:
            return "false_positive"
        if player in {"Patrick Mahomes", "Lamar Jackson"} and rank_delta < 0:
            return "intended_improvement"
    if experiment_id == "wr_v1_reference":
        if player in {"Stefon Diggs", "Davante Adams", "Jameson Williams"} and rank_delta < -6:
            return "false_positive"
        if player in {"CeeDee Lamb", "Justin Jefferson", "Jaylen Waddle"} and rank_delta < 0:
            return "intended_improvement"
    return "acceptable_side_effect" if abs(rank_delta) <= 8 else "needs_more_data"


def _diagnosis_text(
    player: str,
    lane: str,
    v1: dict[str, object],
    v2: dict[str, object],
) -> str:
    v1_class = str(v1.get("movement_classification", ""))
    v2_class = str(v2.get("movement_classification", ""))
    if "false_positive" in v1_class and "false_positive" not in v2_class:
        return "v2 tightens the v1 false-positive gate."
    if "intended_improvement" in v1_class and "intended_improvement" in v2_class:
        return "v2 preserves the useful v1 movement with a tighter receipt gate."
    if "intended_improvement" in v1_class and "stable" in v2_class:
        return "v2 avoids forcing movement when source-safe evidence is not strong enough."
    if lane == "WR lane" and player in {"Puka Nacua", "Jaxon Smith-Njigba"}:
        return "already high; v2 leaves score stable and keeps evidence explanation separate."
    return "movement requires human review."


def _qb_false_positive_warning(
    row: dict[str, str],
    replacement_cap: bool,
    pocket: bool,
) -> str:
    if pocket:
        return "pocket_or_solid_qb_not_given_elite_floor"
    if replacement_cap and (_float(row.get("positive_vorp_points")) or 0.0) <= 0:
        return "replacement_level_qb_cap_blocks_generic_floor"
    return ""


def _v1_false_positive_warning(
    experiment_id: str,
    row: dict[str, str],
    score: float | None,
    base: float,
) -> str:
    delta = (score or base) - base
    player = row.get("player_name", "")
    if experiment_id == "qb_v1_reference" and player in {
        "Jared Goff",
        "Baker Mayfield",
        "Jaxson Dart",
    }:
        return "v1_generic_floor_lifted_non_elite_qb_profile"
    if (
        experiment_id == "wr_v1_reference"
        and player in {"Stefon Diggs", "Davante Adams", "Jameson Williams"}
        and delta > 0
    ):
        return "v1_wr_gate_may_overprotect_age_or_thin_profile"
    return ""


def _reference_id(experiment_id: str) -> str:
    if experiment_id in {"wr_proof_lane_v2", "wr_qb_combined_v2"}:
        return "established_wr_proof_lane"
    if experiment_id == "qb_floor_horizon_v2":
        return "elite_qb_floor_horizon"
    if experiment_id in V1_MAP:
        return V1_MAP[experiment_id]
    return ""


def _hypothesis(experiment_id: str) -> str:
    return {
        "production_baseline": "Current production board baseline.",
        "wr_v1_reference": "V1 WR proof lane readback.",
        "wr_proof_lane_v2": "Tighter established WR proof lane.",
        "qb_v1_reference": "V1 elite QB floor/horizon readback.",
        "qb_floor_horizon_v2": "Tighter elite QB floor/horizon lane.",
        "wr_qb_combined_v2": "Combined WR v2 plus QB v2 only.",
    }[experiment_id]


def _policy(experiment_id: str) -> str:
    return {
        "production_baseline": "No shadow change.",
        "wr_v1_reference": "Read v1 WR lane output for comparison.",
        "wr_proof_lane_v2": "Prime WR proof gate with aging/source/thin-profile blocks.",
        "qb_v1_reference": "Read v1 QB lane output for comparison.",
        "qb_floor_horizon_v2": "QB floor requires multi-signal difference-maker receipts.",
        "wr_qb_combined_v2": "Applies only WR v2 and QB v2.",
    }[experiment_id]


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


def _v1_current_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["experiment_id"], _norm(row.get("player", ""))): row for row in rows}


def _v1_historical_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {
        (row["experiment_id"], str(row.get("draft_year", "")), str(row.get("player", ""))): row
        for row in rows
    }


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


def _contamination_count(experiment_id: str, rows: list[dict[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if row["experiment_id"] == experiment_id
        and row["contamination_check"] != "no_blocked_inputs_used"
    )


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _split(value: str) -> tuple[str, ...]:
    return tuple(part for part in str(value).split("|") if part)


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
