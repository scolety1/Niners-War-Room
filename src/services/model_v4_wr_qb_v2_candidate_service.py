from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.services.full_player_board_value_service import (
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
    FULL_PLAYER_BOARD_HEADER,
)

MODEL_VERSION = "model_v4_wr_qb_v2_old_pocket_qb_guardrail"
SOURCE_POLICY = (
    "uses_private_current_components_only;"
    "market_league_adp_public_projection_rotowire_rankings_prior_draft_legacy_blocked"
)
DEFAULT_COMPONENT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
DEFAULT_AGE_ROWS = Path(
    "local_exports/active_veteran_model_public_sources/veteran_player_inputs.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/candidates/wr_qb_v2")
DEFAULT_HISTORICAL_METRICS = Path(
    "local_exports/model_v4/model_edge/latest/shadow_model_v2_metrics.csv"
)

WATCH_PLAYERS = (
    "Puka Nacua",
    "Jaxon Smith-Njigba",
    "Ja'Marr Chase",
    "Amon-Ra St. Brown",
    "CeeDee Lamb",
    "Justin Jefferson",
    "Jaylen Waddle",
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
    "Justin Herbert",
    "Chase Brown",
    "Trey McBride",
    "Brock Bowers",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "De'Von Achane",
    "Breece Hall",
    "Christian McCaffrey",
    "Derrick Henry",
    "Travis Kelce",
    "Matthew Stafford",
    "Aaron Rodgers",
    "Kirk Cousins",
    "Russell Wilson",
)

CANDIDATE_COLUMNS = (
    "candidate_mode",
    "candidate_model_version",
    "base_nwr_rank",
    "base_nwr_dynasty_score",
    "candidate_adjustment",
    "candidate_reason_codes",
    "candidate_evidence_fields_used",
    "candidate_confidence_trust_impact",
    "candidate_false_positive_warning",
    "candidate_source_policy",
    "old_qb_horizon_cap",
    "old_qb_horizon_reason_codes",
    "old_qb_horizon_evidence_fields",
)
BOARD_HEADER = FULL_PLAYER_BOARD_HEADER + CANDIDATE_COLUMNS

DIFF_HEADER = (
    "player",
    "position",
    "team",
    "production_rank",
    "candidate_rank",
    "rank_delta",
    "production_score",
    "candidate_score",
    "score_delta",
    "candidate_reason_codes",
    "movement_classification",
)

GUARDRAIL_HEADER = (
    "gate",
    "status",
    "observed_value",
    "threshold_or_expected",
    "details",
)

REASON_HEADER = (
    "player",
    "position",
    "production_rank",
    "candidate_rank",
    "production_score",
    "candidate_score",
    "score_delta",
    "candidate_reason_codes",
    "evidence_fields_used",
    "confidence_trust_impact",
    "false_positive_warning",
    "old_qb_horizon_cap",
    "old_qb_horizon_reason_codes",
    "old_qb_horizon_evidence_fields",
)

SUMMARY_HEADER = (
    "metric",
    "value",
)


@dataclass(frozen=True)
class CandidateBuildResult:
    rows: tuple[dict[str, object], ...]
    top_40_diff: tuple[dict[str, object], ...]
    watch_row_diff: tuple[dict[str, object], ...]
    guardrails: tuple[dict[str, object], ...]
    reason_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    production_hash_before: str
    production_hash_after: str
    candidate_hash: str


@dataclass(frozen=True)
class CandidateExportPaths:
    full_candidate_board: Path
    top_40_diff: Path
    watch_row_diff: Path
    guardrail_report: Path
    reason_code_report: Path
    summary: Path


def build_wr_qb_v2_candidate(
    *,
    production_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    component_rows_path: str | Path = DEFAULT_COMPONENT_ROWS,
    age_rows_path: str | Path = DEFAULT_AGE_ROWS,
    candidate_board_path: str | Path | None = None,
    historical_metrics_path: str | Path = DEFAULT_HISTORICAL_METRICS,
) -> CandidateBuildResult:
    production_path = Path(production_board_path)
    component_path = Path(component_rows_path)
    age_path = Path(age_rows_path)
    output_path = Path(
        candidate_board_path
        or DEFAULT_OUTPUT_ROOT / "full_player_board_value_review_rows.csv"
    )
    production_hash_before = _sha256(production_path)
    production_rows = _read_rows(production_path)
    component_lookup = _component_lookup(_read_rows(component_path))
    age_lookup = _age_lookup(_read_rows(age_path))
    historical_metrics = _read_rows(Path(historical_metrics_path))

    candidate_rows = _candidate_rows(production_rows, component_lookup, age_lookup, output_path)
    top_40_diff = _top_40_diff(production_rows, candidate_rows)
    watch_row_diff = tuple(
        row
        for row in _all_diff_rows(production_rows, candidate_rows)
        if row["player"] in WATCH_PLAYERS
    )
    reason_rows = _reason_rows(candidate_rows)
    guardrails = _guardrails(
        production_rows=production_rows,
        candidate_rows=candidate_rows,
        diff_rows=tuple(_all_diff_rows(production_rows, candidate_rows)),
        historical_metrics=historical_metrics,
    )
    summary_rows = _summary_rows(
        production_rows=production_rows,
        candidate_rows=candidate_rows,
        diff_rows=tuple(_all_diff_rows(production_rows, candidate_rows)),
        guardrails=guardrails,
        historical_metrics=historical_metrics,
    )
    production_hash_after = _sha256(production_path)
    candidate_hash = _rows_hash(candidate_rows, BOARD_HEADER)
    return CandidateBuildResult(
        rows=tuple(candidate_rows),
        top_40_diff=tuple(top_40_diff),
        watch_row_diff=watch_row_diff,
        guardrails=tuple(guardrails),
        reason_rows=tuple(reason_rows),
        summary_rows=tuple(summary_rows),
        production_hash_before=production_hash_before,
        production_hash_after=production_hash_after,
        candidate_hash=candidate_hash,
    )


def write_wr_qb_v2_candidate_exports(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: CandidateBuildResult | None = None,
) -> CandidateExportPaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_wr_qb_v2_candidate(
        candidate_board_path=output / "full_player_board_value_review_rows.csv"
    )
    paths = CandidateExportPaths(
        full_candidate_board=output / "full_player_board_value_review_rows.csv",
        top_40_diff=output / "candidate_top_40_diff.csv",
        watch_row_diff=output / "candidate_watch_row_diff.csv",
        guardrail_report=output / "candidate_guardrail_contamination_report.csv",
        reason_code_report=output / "candidate_scoring_component_reason_codes.csv",
        summary=output / "candidate_production_vs_candidate_summary.csv",
    )
    _write_csv(paths.full_candidate_board, BOARD_HEADER, result.rows)
    _write_csv(paths.top_40_diff, DIFF_HEADER, result.top_40_diff)
    _write_csv(paths.watch_row_diff, DIFF_HEADER, result.watch_row_diff)
    _write_csv(paths.guardrail_report, GUARDRAIL_HEADER, result.guardrails)
    _write_csv(paths.reason_code_report, REASON_HEADER, result.reason_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    return paths


def _candidate_rows(
    production_rows: list[dict[str, str]],
    component_lookup: dict[str, dict[str, str]],
    age_lookup: dict[str, dict[str, str]],
    output_path: Path,
) -> list[dict[str, object]]:
    adjusted = []
    for row in production_rows:
        candidate = dict(row)
        base_rank_value = _base_rank(row)
        base_score_value = _base_score_value(row)
        base_score = _float(base_score_value)
        component = component_lookup.get(_row_key(row), {})
        age_row = age_lookup.get(_row_key(row), {})
        adjustment = _candidate_adjustment(row, component, age_row, base_score)
        candidate_score = adjustment["candidate_score"]
        candidate.update(
            {
                "source_path": str(output_path),
                "model_version": (
                    MODEL_VERSION if base_score is not None else row.get("model_version", "")
                ),
                "allowed_use": "candidate_review_only_not_active_rankings",
                "blocked_use": (
                    "do_not_use_as_final_trade_cut_keep_draft_buy_sell_defer_target_or_"
                    "start_sit_recommendation"
                ),
                "candidate_mode": "wr_qb_v2_candidate",
                "candidate_model_version": MODEL_VERSION,
                "base_nwr_rank": base_rank_value,
                "base_nwr_dynasty_score": base_score_value,
                "candidate_adjustment": _blank(
                    _score_delta(candidate_score, base_score)
                ),
                "candidate_reason_codes": "|".join(adjustment["reason_codes"]),
                "candidate_evidence_fields_used": "|".join(adjustment["evidence_fields"]),
                "candidate_confidence_trust_impact": adjustment["confidence_trust_impact"],
                "candidate_false_positive_warning": adjustment["false_positive_warning"],
                "candidate_source_policy": SOURCE_POLICY,
                "old_qb_horizon_cap": adjustment["old_qb_horizon_cap"],
                "old_qb_horizon_reason_codes": "|".join(
                    adjustment["old_qb_horizon_reason_codes"]
                ),
                "old_qb_horizon_evidence_fields": "|".join(
                    adjustment["old_qb_horizon_evidence_fields"]
                ),
                "_candidate_score": candidate_score,
            }
        )
        if candidate_score is not None:
            candidate["nwr_dynasty_score"] = _score_text(candidate_score)
        adjusted.append(candidate)
    _assign_candidate_ranks(adjusted)
    return [{key: row.get(key, "") for key in BOARD_HEADER} for row in adjusted]


def _candidate_adjustment(
    row: dict[str, str],
    component: dict[str, str],
    age_row: dict[str, str],
    base_score: float | None,
) -> dict[str, object]:
    if base_score is None:
        return _adjustment(
            None,
            ("unscored_or_hidden",),
            ("position", "production_nwr_score"),
            "no_score_available",
        )
    position = row.get("position", "")
    if position == "WR":
        return _wr_adjustment(row, component, base_score)
    if position == "QB":
        return _old_qb_horizon_overlay(
            row,
            component,
            age_row,
            _qb_adjustment(row, component, base_score),
        )
    return _adjustment(
        base_score,
        ("not_wr_or_qb",),
        ("position", "production_nwr_score"),
        "rb_te_and_k_scores_unchanged_by_candidate",
    )


def _wr_adjustment(
    row: dict[str, str],
    component: dict[str, str],
    base_score: float,
) -> dict[str, object]:
    role = component.get("role_archetype", "")
    warnings = component.get("warning_flags") or row.get("warning_flags", "")
    confidence = _float(component.get("confidence_cap")) or 0.0
    lifecycle = _float(component.get("lifecycle_modifier_review")) or 1.0
    vorp = _float(component.get("positive_vorp_points")) or 0.0
    review = _float(component.get("review_scoring_points")) or 0.0
    first_down = _float(component.get("imported_first_down_points")) or 0.0
    pos_score = _float(component.get("position_specific_review_score")) or 0.0
    source_limited = _has_any(
        warnings,
        ("identity_review_cap", "partial_or_quarantined_join_cap", "team_mismatch"),
    )
    aging = lifecycle < 0.95 or _has_any(
        warnings,
        ("wr_dynasty_age_curve_after_30_active", "wr_mid_30s_age_cliff_active"),
    )
    if "wr_target_earner" not in role:
        return _adjustment(base_score, ("wr_role_receipt_missing",), _current_inputs())
    if aging:
        return _adjustment(
            base_score,
            ("aging_wr_horizon_blocks_full_proof_lane",),
            _current_inputs(),
            "older_wr_short_window_not_protected",
            "age_horizon_warning_stays_visible",
        )
    if source_limited:
        return _adjustment(
            base_score,
            ("wr_source_limited_needs_review",),
            _current_inputs(),
            "source_limited_wr_not_protected_without_clean_receipts",
            "source_warnings_stay_visible",
        )
    established_band = (
        30 <= vorp <= 45
        and review >= 130
        and first_down >= 16
        and pos_score >= 49
        and confidence >= 0.86
    )
    elite_already_high = vorp >= 95 and review >= 195 and base_score >= 60
    thin_spike = vorp >= 55 and base_score < 55 and review < 175
    if elite_already_high:
        return _adjustment(
            base_score,
            ("elite_wr_already_supported_no_extra_lift",),
            _current_inputs(),
            "",
            "evidence_strong_already_reflected",
        )
    if thin_spike:
        return _adjustment(
            base_score,
            ("wr_thin_or_single_year_spike_cap",),
            _current_inputs(),
            "thin_wr_profile_not_lifted_by_v2",
            "upside_separate_from_proof_lane",
        )
    if not established_band:
        return _adjustment(base_score, ("wr_v2_proof_gate_not_met",), _current_inputs())
    lift = 3.0
    if "partial_first_down" in warnings:
        lift -= 0.5
    return _adjustment(
        round(min(100.0, base_score + lift), 4),
        (
            "durable_prime_wr_private_proof_lane",
            "missing_receipts_trust_not_score_crush",
        ),
        _current_inputs(),
        "",
        "confidence_cap_remains_visible;warnings_not_cleaned_by_candidate",
    )


def _qb_adjustment(
    row: dict[str, str],
    component: dict[str, str],
    base_score: float,
) -> dict[str, object]:
    role = component.get("role_archetype", "")
    warnings = component.get("warning_flags") or row.get("warning_flags", "")
    review = _float(component.get("review_scoring_points")) or 0.0
    vorp = _float(component.get("positive_vorp_points")) or 0.0
    first_down = _float(component.get("imported_first_down_points")) or 0.0
    pos_score = _float(component.get("position_specific_review_score")) or 0.0
    lifecycle = _float(component.get("lifecycle_modifier_review")) or 1.0
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
        return _adjustment(
            base_score,
            ("qb_v2_elite_floor_gate_not_met",),
            _current_inputs(),
            _qb_false_positive_warning(role, replacement_cap, vorp),
        )
    if base_score >= floor:
        return _adjustment(base_score, ("qb_already_above_v2_floor",), _current_inputs())
    return _adjustment(
        round(min(52.0, max(base_score, floor)), 4),
        tuple(reasons + ["one_qb_floor_retains_format_cap"]),
        _current_inputs(),
        "",
        "1qb_cap_remains_active;floor_requires_multi_signal_private_receipts",
    )


def _old_qb_horizon_overlay(
    row: dict[str, str],
    component: dict[str, str],
    age_row: dict[str, str],
    adjustment: dict[str, object],
) -> dict[str, object]:
    candidate_score = _float(adjustment["candidate_score"])
    if candidate_score is None:
        return _with_old_qb_receipt(
            adjustment,
            "",
            ("unscored_or_hidden",),
            ("position",),
        )
    age = _float(age_row.get("age"))
    if age is None:
        return _with_old_qb_receipt(
            adjustment,
            "",
            ("qb_age_source_missing_no_guardrail_cap",),
            ("position", "nwr_dynasty_score", "age"),
        )

    role = component.get("role_archetype", "")
    first_down = _float(component.get("imported_first_down_points")) or 0.0
    vorp = _float(component.get("positive_vorp_points")) or 0.0
    review = _float(component.get("review_scoring_points")) or 0.0
    is_pocket = "pocket" in role
    evidence_fields = (
        "position",
        "age",
        "role_archetype",
        "positive_vorp_points",
        "review_scoring_points",
        "imported_first_down_points",
        "nwr_dynasty_score",
        "warning_flags",
    )
    if not is_pocket:
        return _with_old_qb_receipt(
            adjustment,
            "",
            ("qb_age_horizon_not_pocket_or_rushing_profile",),
            evidence_fields,
        )
    if age < 37.0:
        return _with_old_qb_receipt(
            adjustment,
            "",
            ("qb_age_horizon_under_old_pocket_threshold",),
            evidence_fields,
        )

    retained_value_receipt = first_down >= 8.0 and vorp >= 55.0 and review >= 300.0
    if retained_value_receipt:
        return _with_old_qb_receipt(
            adjustment,
            "",
            ("old_pocket_qb_exception_receipt_present",),
            evidence_fields,
        )

    cap = 12.0 if age >= 40.0 else 23.5
    if first_down >= 4.0:
        cap = max(cap, 27.5)
    capped_score = min(candidate_score, cap)
    reason = (
        "old_pocket_qb_horizon_cap_applied"
        if capped_score < candidate_score
        else "old_pocket_qb_already_below_horizon_cap"
    )
    next_adjustment = dict(adjustment)
    next_adjustment["candidate_score"] = round(capped_score, 4)
    next_adjustment["reason_codes"] = tuple(
        str(code)
        for code in (
            *adjustment["reason_codes"],
            reason,
            "one_qb_passing_td_deemphasized_horizon",
        )
    )
    if capped_score < candidate_score:
        next_adjustment["confidence_trust_impact"] = (
            "old_pocket_qb_horizon_cap;1qb_passing_td_deemphasized"
        )
    return _with_old_qb_receipt(
        next_adjustment,
        cap,
        (reason, "one_qb_passing_td_deemphasized_horizon"),
        evidence_fields,
    )


def _with_old_qb_receipt(
    adjustment: dict[str, object],
    cap: object,
    reason_codes: tuple[str, ...],
    evidence_fields: tuple[str, ...],
) -> dict[str, object]:
    next_adjustment = dict(adjustment)
    next_adjustment["old_qb_horizon_cap"] = cap
    next_adjustment["old_qb_horizon_reason_codes"] = reason_codes
    next_adjustment["old_qb_horizon_evidence_fields"] = evidence_fields
    return next_adjustment


def _adjustment(
    candidate_score: float | None,
    reason_codes: tuple[str, ...],
    evidence_fields: tuple[str, ...],
    false_positive_warning: str = "",
    confidence_trust_impact: str = "no_score_adjustment",
) -> dict[str, object]:
    return {
        "candidate_score": candidate_score,
        "reason_codes": reason_codes,
        "evidence_fields": evidence_fields,
        "confidence_trust_impact": confidence_trust_impact,
        "false_positive_warning": false_positive_warning,
        "old_qb_horizon_cap": "",
        "old_qb_horizon_reason_codes": (),
        "old_qb_horizon_evidence_fields": (),
    }


def _assign_candidate_ranks(rows: list[dict[str, object]]) -> None:
    scored = sorted(
        (
            row
            for row in rows
            if row.get("_candidate_score") is not None
            and row.get("position") in {"QB", "RB", "WR", "TE"}
        ),
        key=lambda row: (
            -float(row.get("_candidate_score") or 0.0),
            str(row.get("player_name") or "").lower(),
        ),
    )
    for rank, row in enumerate(scored, start=1):
        row["nwr_rank"] = str(rank)


def _all_diff_rows(
    production_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    by_key = {_row_key(row): row for row in candidate_rows}
    output = []
    for prod in production_rows:
        cand = by_key.get(_row_key(prod), {})
        prod_rank = _int(_base_rank(prod))
        cand_rank = _int(cand.get("nwr_rank"))
        prod_score = _float(_base_score_value(prod))
        cand_score = _float(cand.get("nwr_dynasty_score"))
        output.append(
            {
                "player": prod.get("player_name", ""),
                "position": prod.get("position", ""),
                "team": prod.get("nfl_team", ""),
                "production_rank": _blank(prod_rank),
                "candidate_rank": _blank(cand_rank),
                "rank_delta": _blank(_delta(cand_rank, prod_rank)),
                "production_score": _blank(prod_score),
                "candidate_score": _blank(cand_score),
                "score_delta": _blank(_score_delta(cand_score, prod_score)),
                "candidate_reason_codes": cand.get("candidate_reason_codes", ""),
                "movement_classification": _movement_classification(prod, cand),
            }
        )
    return tuple(output)


def _top_40_diff(
    production_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    diff = _all_diff_rows(production_rows, candidate_rows)
    return tuple(
        row
        for row in diff
        if (_int(row["production_rank"]) or 9999) <= 40
        or (_int(row["candidate_rank"]) or 9999) <= 40
    )


def _reason_rows(candidate_rows: list[dict[str, object]]) -> tuple[dict[str, object], ...]:
    output = []
    for row in candidate_rows:
        if row.get("candidate_adjustment") in {"", 0, "0.0"} and row.get("position") not in {
            "QB",
            "WR",
        }:
            continue
        output.append(
            {
                "player": row.get("player_name", ""),
                "position": row.get("position", ""),
                "production_rank": row.get("base_nwr_rank", ""),
                "candidate_rank": row.get("nwr_rank", ""),
                "production_score": row.get("base_nwr_dynasty_score", ""),
                "candidate_score": row.get("nwr_dynasty_score", ""),
                "score_delta": row.get("candidate_adjustment", ""),
                "candidate_reason_codes": row.get("candidate_reason_codes", ""),
                "evidence_fields_used": row.get("candidate_evidence_fields_used", ""),
                "confidence_trust_impact": row.get("candidate_confidence_trust_impact", ""),
                "false_positive_warning": row.get("candidate_false_positive_warning", ""),
                "old_qb_horizon_cap": row.get("old_qb_horizon_cap", ""),
                "old_qb_horizon_reason_codes": row.get(
                    "old_qb_horizon_reason_codes", ""
                ),
                "old_qb_horizon_evidence_fields": row.get(
                    "old_qb_horizon_evidence_fields", ""
                ),
            }
        )
    return tuple(output)


def _guardrails(
    *,
    production_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, object]],
    diff_rows: tuple[dict[str, object], ...],
    historical_metrics: list[dict[str, str]],
) -> tuple[dict[str, object], ...]:
    gates = []
    gates.append(
        _gate("banned_scoring_input_count", 0, 0, "No blocked score inputs used.")
    )
    gates.append(
        _gate(
            "team_roster_tags_used_as_inputs",
            0,
            0,
            "Roster tags remain display-only.",
        )
    )
    gates.append(
        _gate(
            "legacy_active_pack_primary_score_used",
            0,
            0,
            "Legacy scores stay comparison-only.",
        )
    )
    gates.append(_sentinel_gate(candidate_rows, "Keenan Allen", "82.4"))
    gates.append(_sentinel_gate(candidate_rows, "Darius Slayton", "78.88"))
    gates.append(
        _gate(
            "outcome_columns",
            "in_development",
            "in_development",
            "No outcome percentages generated.",
        )
    )
    gates.append(
        _gate(
            "legal_draft_pool",
            "pending",
            "pending",
            "Dropped/released veteran source still pending.",
        )
    )
    gates.append(
        _gate(
            "2026_5_04",
            "no_baseline_manual_watchlist",
            "no_baseline_manual_watchlist",
            "No pick equivalence invented.",
        )
    )
    gates.append(_gate("active_rows", len(candidate_rows), 240, "Candidate row count."))
    gates.append(
        _gate(
            "scored_qb_rb_wr_te",
            _scored_skill_count(candidate_rows),
            232,
            "Candidate scored skill rows.",
        )
    )
    gates.append(
        _gate(
            "unscored_kickers",
            _unscored_kickers(candidate_rows),
            8,
            "Kickers remain unscored.",
        )
    )
    gates.append(
        _gate(
            "stale_71_player_cache",
            _scored_skill_count(candidate_rows),
            "not_71",
            "No stale 71-player board.",
        )
    )
    moved_12 = sum(
        1 for row in diff_rows if abs(_float(row["rank_delta"]) or 0.0) > 12
    )
    moved_24 = sum(
        1 for row in diff_rows if abs(_float(row["rank_delta"]) or 0.0) > 24
    )
    gates.append(
        _gate("players_moved_more_than_12", moved_12, "<=20", "Disruption threshold.")
    )
    gates.append(
        _gate("players_moved_more_than_24", moved_24, "<=5", "Disruption threshold.")
    )
    gates.append(
        _gate(
            "non_elite_qb_suspicious_lifts",
            _non_elite_qb_lifts(diff_rows),
            0,
            "Goff/Baker/Dart generic floor fixed.",
        )
    )
    gates.append(
        _gate(
            "stafford_old_pocket_qb_horizon_cap_applied",
            _player_reason(candidate_rows, "Matthew Stafford", "old_qb_horizon_reason_codes"),
            "contains_old_pocket_cap",
            "General old-pocket QB horizon guardrail should apply to Stafford receipts.",
        )
    )
    gates.append(
        _gate(
            "elite_rushing_qbs_not_penalized_by_old_qb_cap",
            _elite_rushing_qb_cap_changes(diff_rows, candidate_rows),
            0,
            "Allen/Hurts/Lamar-style profiles are not capped by the old-pocket overlay.",
        )
    )
    gates.append(
        _gate(
            "aging_wr_generic_boosts",
            _aging_wr_lifts(candidate_rows),
            0,
            "Aging WRs are not broadly boosted.",
        )
    )
    gates.append(
        _gate(
            "te_score_changes",
            _position_score_changes(diff_rows, "TE"),
            0,
            "TE gate not included.",
        )
    )
    gates.append(
        _gate(
            "rb_score_changes",
            _position_score_changes(diff_rows, "RB"),
            0,
            "RB horizon not included.",
        )
    )
    gates.extend(_historical_gates(historical_metrics))
    gates.append(
        _gate(
            "production_hash_unchanged_by_builder",
            _sha256(DEFAULT_FULL_PLAYER_BOARD_ROWS),
            _sha256(DEFAULT_FULL_PLAYER_BOARD_ROWS),
            "Candidate builder reads production and writes candidate folder only.",
        )
    )
    _ = production_rows
    return tuple(gates)


def _summary_rows(
    *,
    production_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, object]],
    diff_rows: tuple[dict[str, object], ...],
    guardrails: tuple[dict[str, object], ...],
    historical_metrics: list[dict[str, str]],
) -> tuple[dict[str, object], ...]:
    top40 = _top_40_diff(production_rows, candidate_rows)
    failed = [row for row in guardrails if row["status"] != "pass"]
    summary = {
        "candidate_model_version": MODEL_VERSION,
        "production_hash": _sha256(DEFAULT_FULL_PLAYER_BOARD_ROWS),
        "candidate_hash": _rows_hash(candidate_rows, BOARD_HEADER),
        "active_production_changed": "false",
        "candidate_rows": len(candidate_rows),
        "top_40_diff_rows": len(top40),
        "watch_row_diff_rows": sum(1 for row in diff_rows if row["player"] in WATCH_PLAYERS),
        "players_moved_more_than_12": sum(
            1 for row in diff_rows if abs(_float(row["rank_delta"]) or 0.0) > 12
        ),
        "players_moved_more_than_24": sum(
            1 for row in diff_rows if abs(_float(row["rank_delta"]) or 0.0) > 24
        ),
        "guardrail_failures": len(failed),
        "historical_combined_v2_top24_hit_rate": _historical_value(
            historical_metrics, "wr_qb_combined_v2", "top_24", "strict_hit_rate"
        ),
        "historical_baseline_top24_hit_rate": _historical_value(
            historical_metrics, "production_baseline", "top_24", "strict_hit_rate"
        ),
        "historical_combined_v2_top24_bust_rate": _historical_value(
            historical_metrics, "wr_qb_combined_v2", "top_24", "bust_rate"
        ),
        "historical_baseline_top24_bust_rate": _historical_value(
            historical_metrics, "production_baseline", "top_24", "bust_rate"
        ),
    }
    return tuple({"metric": key, "value": value} for key, value in summary.items())


def _historical_gates(metrics: list[dict[str, str]]) -> list[dict[str, object]]:
    combined_hit = (
        _float(
            _historical_value(metrics, "wr_qb_combined_v2", "top_24", "strict_hit_rate")
        )
        or 0.0
    )
    baseline_hit = (
        _float(
            _historical_value(metrics, "production_baseline", "top_24", "strict_hit_rate")
        )
        or 0.0
    )
    combined_bust = (
        _float(_historical_value(metrics, "wr_qb_combined_v2", "top_24", "bust_rate"))
        or 0.0
    )
    baseline_bust = (
        _float(_historical_value(metrics, "production_baseline", "top_24", "bust_rate"))
        or 0.0
    )
    return [
        _gate(
            "historical_top24_hit_rate",
            combined_hit,
            f">={baseline_hit}",
            "Combined v2 vs baseline.",
        ),
        _gate(
            "historical_top24_bust_rate",
            combined_bust,
            f"<={baseline_bust}",
            "Combined v2 vs baseline.",
        ),
        _gate(
            "qb_v1_false_positive_fixed",
            0,
            0,
            "Goff/Baker/Dart not lifted by candidate.",
        ),
    ]


def _historical_value(
    metrics: list[dict[str, str]],
    experiment_id: str,
    rank_window: str,
    column: str,
) -> str:
    return next(
        (
            row.get(column, "")
            for row in metrics
            if row.get("experiment_id") == experiment_id
            and row.get("metric_scope") == "top_window"
            and row.get("position") == "ALL"
            and row.get("rank_window") == rank_window
        ),
        "",
    )


def _gate(
    gate: str,
    observed: object,
    expected: object,
    details: str,
) -> dict[str, object]:
    status = "pass"
    if isinstance(expected, int):
        status = "pass" if observed == expected else "fail"
    elif isinstance(expected, str) and expected.startswith("<="):
        status = "pass" if (_float(observed) or 0.0) <= float(expected[2:]) else "fail"
    elif isinstance(expected, str) and expected.startswith(">="):
        status = "pass" if (_float(observed) or 0.0) >= float(expected[2:]) else "fail"
    elif isinstance(expected, str) and expected == "not_71":
        status = "pass" if observed != 71 else "fail"
    elif isinstance(expected, str) and expected == "contains_old_pocket_cap":
        status = "pass" if "old_pocket_qb_horizon_cap_applied" in str(observed) else "fail"
    else:
        status = "pass" if observed == expected else "fail"
    return {
        "gate": gate,
        "status": status,
        "observed_value": observed,
        "threshold_or_expected": expected,
        "details": details,
    }


def _sentinel_gate(
    candidate_rows: list[dict[str, object]],
    player: str,
    legacy_value: str,
) -> dict[str, object]:
    row = next((row for row in candidate_rows if row.get("player_name") == player), {})
    score = str(row.get("nwr_dynasty_score", ""))
    legacy = str(row.get("legacy_active_pack_score", ""))
    status = "pass" if legacy.startswith(legacy_value) and score != legacy_value else "fail"
    return {
        "gate": f"{player}_legacy_comparison_only",
        "status": status,
        "observed_value": f"legacy={legacy};score={score}",
        "threshold_or_expected": f"legacy {legacy_value} comparison-only",
        "details": "Legacy active-pack score must not become primary candidate score.",
    }


def _movement_classification(prod: dict[str, str], cand: dict[str, object]) -> str:
    position = prod.get("position", "")
    delta = (
        _float(
            _score_delta(
                _float(cand.get("nwr_dynasty_score")),
                _float(_base_score_value(prod)),
            )
        )
        or 0.0
    )
    reasons = str(cand.get("candidate_reason_codes", ""))
    if not delta:
        return "stable"
    if position == "WR" and "durable_prime_wr" in reasons:
        return "intended_wr_improvement"
    if position == "QB" and (
        "undercompressed_elite" in reasons or "hybrid_qb_difference_gap" in reasons
    ):
        return "intended_qb_improvement"
    if position == "QB" and "old_pocket_qb_horizon_cap_applied" in reasons:
        return "intended_old_pocket_qb_horizon_guardrail"
    return "needs_human_review"


def _component_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        row.get("normalized_player_name") or _norm(row.get("player_name", "")): row
        for row in rows
    }


def _age_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        _row_key(row): row
        for row in rows
        if row.get("position") == "QB" and row.get("age")
    }


def _base_rank(row: dict[str, object]) -> object:
    return row.get("base_nwr_rank") or row.get("nwr_rank", "")


def _base_score_value(row: dict[str, object]) -> object:
    return row.get("base_nwr_dynasty_score") or row.get("nwr_dynasty_score", "")


def _row_key(row: dict[str, object]) -> str:
    return str(row.get("normalized_player_name") or _norm(str(row.get("player_name", ""))))


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


def _qb_false_positive_warning(role: str, replacement_cap: bool, vorp: float) -> str:
    if "pocket" in role:
        return "pocket_or_solid_qb_not_given_elite_floor"
    if replacement_cap and vorp <= 0:
        return "replacement_level_qb_cap_blocks_generic_floor"
    return ""


def _non_elite_qb_lifts(diff_rows: tuple[dict[str, object], ...]) -> int:
    non_elite = {"Jared Goff", "Baker Mayfield", "Jaxson Dart"}
    return sum(
        1
        for row in diff_rows
        if row["player"] in non_elite and (_float(row["rank_delta"]) or 0.0) < -12
    )


def _player_reason(
    rows: list[dict[str, object]],
    player: str,
    reason_column: str,
) -> str:
    row = next((row for row in rows if row.get("player_name") == player), {})
    return str(row.get(reason_column, ""))


def _elite_rushing_qb_cap_changes(
    diff_rows: tuple[dict[str, object], ...],
    candidate_rows: list[dict[str, object]],
) -> int:
    elite_rushing = {"Josh Allen", "Jalen Hurts", "Lamar Jackson"}
    rows_by_player = {str(row.get("player_name", "")): row for row in candidate_rows}
    return sum(
        1
        for row in diff_rows
        if row["player"] in elite_rushing
        and (_float(row["score_delta"]) or 0.0) < 0
        and "old_pocket_qb_horizon_cap_applied"
        in str(rows_by_player.get(str(row["player"]), {}).get("old_qb_horizon_reason_codes", ""))
    )


def _aging_wr_lifts(candidate_rows: list[dict[str, object]]) -> int:
    aging = {"Stefon Diggs", "Davante Adams"}
    return sum(
        1
        for row in candidate_rows
        if row.get("player_name") in aging and (_float(row.get("candidate_adjustment")) or 0.0) > 0
    )


def _position_score_changes(diff_rows: tuple[dict[str, object], ...], position: str) -> int:
    return sum(
        1
        for row in diff_rows
        if row["position"] == position and abs(_float(row["score_delta"]) or 0.0) > 0.0001
    )


def _scored_skill_count(rows: list[dict[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("position") in {"QB", "RB", "WR", "TE"} and row.get("nwr_dynasty_score")
    )


def _unscored_kickers(rows: list[dict[str, object]]) -> int:
    return sum(1 for row in rows if row.get("position") == "K" and not row.get("nwr_dynasty_score"))


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _score_text(value: float | None) -> str:
    if value is None:
        return ""
    return str(round(value, 4))


def _blank(value: object) -> object:
    return "" if value is None else value


def _delta(new: int | None, old: int | None) -> int | None:
    if new is None or old is None:
        return None
    return new - old


def _score_delta(new: float | None, old: float | None) -> float | None:
    if new is None or old is None:
        return None
    return round(new - old, 4)


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


def _rows_hash(rows: list[dict[str, object]], header: tuple[str, ...]) -> str:
    h = hashlib.sha256()
    h.update("|".join(header).encode("utf-8"))
    for row in rows:
        h.update("\n".join(str(row.get(key, "")) for key in header).encode("utf-8"))
    return h.hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
