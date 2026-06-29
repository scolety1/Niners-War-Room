from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.model_v4_player_identity_crosswalk_service import (  # noqa: E402
    normalize_identity_name,
)

NFLVERSE_PYDEPS = Path(r"C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps")
if str(NFLVERSE_PYDEPS) not in sys.path:
    sys.path.insert(0, str(NFLVERSE_PYDEPS))

DOC_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_coverage_repair_v2_20260630"
)
SHARED_DISPLAY_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\display_artifact_v3")

PREVIOUS_REPAIR_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_source_expansion_coverage_runner_v1_20260630"
    / "rookie_draft_capital_repair_coverage_matrix_v1.csv"
)
PREVIOUS_DISPLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_source_expansion_coverage_runner_v1_20260630"
    / "rookie_display_artifact_v2_coverage_matrix.csv"
)
GATE_A_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
    / "cfbd_rookie_identity_human_approval_v1.csv"
)
GATE_E_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_e_model_rd_v1_20260630"
    / "rookie_model_rd_validation_summary_v1.csv"
)
GATE_E_METRICS_PATH = (
    Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\model_rd_v1")
    / "rookie_model_rd_validation_metrics_v1.csv"
)
HISTORICAL_LABEL_PATH = (
    Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1")
    / "rookie_historical_outcome_labels_v1.csv"
)
SOURCE_REGISTRY_PATH = REPO_ROOT / "config" / "source_registry.csv"

BASE_HEAD = "8047764ad45b3c7e43f3ac0a03c2c3386f2f6012"
RUN_ID = "rookie_draft_capital_coverage_repair_v2_20260630"
NOT_ENOUGH = "Not enough information"
CURRENT_DRAFT_YEARS = (2025, 2026)
DIAGNOSTIC_DRAFT_YEARS = tuple(range(2012, 2027))
SKILL_POSITIONS = {"QB", "RB", "WR", "TE"}

TARGETS = tuple(
    f"{horizon}_top_{threshold}_hit"
    for horizon in ("rookie_year", "year_2", "first_3y", "first_5y")
    for threshold in (12, 24, 36)
)
POSITION_SUPPORTED_THRESHOLDS = {
    "QB": {12},
    "RB": {12, 24, 36},
    "WR": {12, 24, 36},
    "TE": {12},
}

DIAGNOSIS_COLUMNS = (
    "player_name",
    "player_id",
    "position",
    "team",
    "cfbd_identity_status",
    "current_draft_capital_status",
    "nflverse_draft_pick_match_status",
    "name_normalization_status",
    "position_match_status",
    "team_or_school_match_status",
    "class_year_status",
    "possible_drafted_match_candidates",
    "likely_udfa_undrafted_candidate_status",
    "blocker_category",
    "blocker_reason",
    "recommended_repair_action",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

REPAIR_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "draft_pick",
    "overall_pick",
    "drafted_team",
    "draft_capital_bucket",
    "draft_capital_source",
    "draft_capital_provenance",
    "draft_capital_status",
    "udffa_or_undrafted_status",
    "udffa_or_undrafted_source",
    "repair_action",
    "repair_confidence",
    "data_quality_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

FEATURE_COLUMNS = (
    "feature_family",
    "feature_name",
    "source",
    "availability_status",
    "approval_status",
    "allowed_for_review_only_model_rd",
    "allowed_for_display_context",
    "model_use_allowed",
    "training_allowed",
    "review_only",
    "leakage_risk",
    "missingness_risk",
    "blocker_reason",
    "required_next_gate",
    "notes",
)

DISPLAY_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "draft_pick",
    "overall_pick",
    "draft_capital_bucket",
    "udffa_or_undrafted_status",
    "identity_status",
    "draft_capital_status",
    "feature_coverage_status",
    "model_rd_status",
    "validation_status",
    "display_status",
    "data_quality_status",
    "source_provenance_status",
    "repair_action",
    "repair_confidence",
    "rookie_year_top_12_review_display_rate",
    "rookie_year_top_24_review_display_rate",
    "rookie_year_top_36_review_display_rate",
    "year_2_top_12_review_display_rate",
    "year_2_top_24_review_display_rate",
    "year_2_top_36_review_display_rate",
    "first_3y_top_12_review_display_rate",
    "first_3y_top_24_review_display_rate",
    "first_3y_top_36_review_display_rate",
    "first_5y_top_12_review_display_rate",
    "first_5y_top_24_review_display_rate",
    "first_5y_top_36_review_display_rate",
    "display_field_count",
    "not_enough_information_field_count",
    "rate_method_summary",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
    "notes",
)

SUMMARY_COLUMNS = (
    "metric",
    "value",
    "notes",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-root", type=Path, default=DOC_ROOT)
    args = parser.parse_args(argv)

    args.doc_root.mkdir(parents=True, exist_ok=True)
    SHARED_DISPLAY_ROOT.mkdir(parents=True, exist_ok=True)

    previous_repair_rows = read_csv(PREVIOUS_REPAIR_PATH)
    previous_display_rows = read_csv(PREVIOUS_DISPLAY_PATH)
    gate_a_rows = read_csv(GATE_A_PATH)
    gate_e_summary = read_csv(GATE_E_SUMMARY_PATH)
    gate_e_metrics = read_csv(GATE_E_METRICS_PATH)
    historical_labels = read_csv(HISTORICAL_LABEL_PATH)
    source_registry_rows = read_csv(SOURCE_REGISTRY_PATH)

    current_draft_picks = load_nflverse_draft_picks(CURRENT_DRAFT_YEARS)
    diagnostic_draft_picks = load_nflverse_draft_picks(DIAGNOSTIC_DRAFT_YEARS)

    gate_a_index = build_gate_a_index(gate_a_rows)
    current_index = build_draft_index(current_draft_picks)
    diagnostic_index = build_draft_index(diagnostic_draft_picks)
    diagnostic_name_index = build_name_index(diagnostic_draft_picks)

    missing_rows = [
        row
        for row in previous_repair_rows
        if row["draft_capital_status"].startswith("MISSING")
    ]
    diagnosis_rows = build_missingness_diagnosis_rows(
        missing_rows,
        gate_a_index,
        current_index,
        diagnostic_index,
        diagnostic_name_index,
    )
    repair_rows = build_repair_rows(
        previous_repair_rows,
        gate_a_index,
        current_index,
        diagnostic_index,
        diagnostic_name_index,
    )
    feature_rows = build_feature_policy_rows()
    display_rows = build_display_rows(
        repair_rows,
        historical_labels,
        gate_e_summary,
        gate_e_metrics,
    )
    display_summary_rows = build_display_summary_rows(display_rows)

    write_csv(
        args.doc_root / "rookie_draft_capital_missingness_diagnosis_v2.csv",
        DIAGNOSIS_COLUMNS,
        diagnosis_rows,
    )
    write_csv(
        args.doc_root / "rookie_draft_capital_repair_v2_matrix.csv",
        REPAIR_COLUMNS,
        repair_rows,
    )
    write_csv(
        args.doc_root / "rookie_feature_policy_draft_capital_v2_matrix.csv",
        FEATURE_COLUMNS,
        feature_rows,
    )
    write_csv(
        args.doc_root / "rookie_display_artifact_v3_coverage_matrix.csv",
        DISPLAY_COLUMNS,
        display_rows,
    )

    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_artifact_v3.csv",
        DISPLAY_COLUMNS,
        display_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_coverage_summary_v3.csv",
        SUMMARY_COLUMNS,
        display_summary_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_manifest_v3.csv",
        SUMMARY_COLUMNS,
        shared_manifest_rows("display_artifact_v3", len(display_rows)),
    )

    write_docs(
        args.doc_root,
        previous_repair_rows,
        previous_display_rows,
        gate_e_metrics,
        source_registry_rows,
        current_draft_picks,
        diagnosis_rows,
        repair_rows,
        feature_rows,
        display_rows,
    )

    print(
        {
            "final_verdict": "PARTIAL_DRAFT_CAPITAL_COVERAGE_REPAIR_V2",
            "diagnosed_missing_rows": len(diagnosis_rows),
            "drafted_display_rows_v3": count_display_rows(display_rows),
            "not_enough_information_rows_v3": count_not_enough_rows(display_rows),
            "confirmed_udfa_rows": count_udfa_status(repair_rows, "confirmed_udfa"),
            "likely_udfa_rows": count_udfa_status(repair_rows, "likely_udfa_needs_review"),
            "gate_g": "BLOCKED_NEEDS_DISPLAY_COVERAGE",
        }
    )


def build_missingness_diagnosis_rows(
    missing_rows: list[dict[str, str]],
    gate_a_index: dict[tuple[str, str, str], dict[str, str]],
    current_index: dict[tuple[str, str], list[dict[str, str]]],
    diagnostic_index: dict[tuple[str, str], list[dict[str, str]]],
    diagnostic_name_index: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    rows = []
    for row in missing_rows:
        key = draft_key(row)
        gate_a = gate_a_for_row(row, gate_a_index)
        current_matches = current_index.get(key, [])
        diagnostic_matches = diagnostic_index.get(key, [])
        older_matches = [
            match
            for match in diagnostic_matches
            if to_int(match["season"]) is not None
            and to_int(match["season"]) < min(CURRENT_DRAFT_YEARS)
        ]
        name_matches = diagnostic_name_index.get(normalize_identity_name(row["player_name"]), [])
        likely_status = likely_udfa_status(row, gate_a, bool(current_matches), bool(older_matches))
        if current_matches:
            category = "drafted_join_miss"
            match_status = "exact_name_position_match_in_2025_2026_nflverse_draft_picks"
            blocker = "V1 used an incomplete draft-year window; nflverse has safe match."
            action = "repair_with_nflverse_2025_2026_exact_name_position_match"
            position_status = "exact_position_match"
            class_status = "rookie_class_year_repaired_from_nflverse_draft_season"
        elif older_matches:
            category = "not_draft_eligible_or_wrong_universe"
            match_status = "older_nfl_draft_match_not_current_rookie_class"
            blocker = "Exact name + position matched an older NFL draftee; keep blocked."
            action = "block_and_require_identity_or_universe_review"
            position_status = "exact_position_match_to_older_nfl_draftee"
            class_status = "current_rookie_class_mismatch"
        elif name_matches:
            category = "position_mismatch"
            match_status = "name_match_only_position_mismatch"
            blocker = "Name appears in nflverse draft picks but not at the approved position."
            action = "block_and_require_human_identity_review"
            position_status = "position_mismatch"
            class_status = "not_enough_information"
        elif likely_status == "likely_udfa_needs_review":
            category = "likely_udfa_needs_source"
            match_status = "no_current_nflverse_draft_pick_match"
            blocker = "NWR/Sleeper team context exists, but draft-pick absence is not UDFA proof."
            action = "leave_as_udfa_review_needed_without_display_rates"
            position_status = "not_enough_information"
            class_status = "not_enough_information"
        else:
            category = "needs_human_review"
            match_status = "no_safe_draft_pick_match"
            blocker = "No safe draft-pick or approved UDFA source was found."
            action = "leave_as_not_enough_information"
            position_status = "not_enough_information"
            class_status = "not_enough_information"

        rows.append(
            {
                "player_name": clean(row["player_name"]),
                "player_id": clean(row["player_id"]),
                "position": clean(row["position"]),
                "team": gate_a_team(gate_a),
                "cfbd_identity_status": clean(
                    gate_a.get("gate_a_status", "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL")
                ),
                "current_draft_capital_status": clean(row["draft_capital_status"]),
                "nflverse_draft_pick_match_status": match_status,
                "name_normalization_status": normalize_identity_name(row["player_name"]),
                "position_match_status": position_status,
                "team_or_school_match_status": team_or_school_status(gate_a, current_matches),
                "class_year_status": class_status,
                "possible_drafted_match_candidates": format_candidates(
                    current_matches or older_matches or name_matches
                ),
                "likely_udfa_undrafted_candidate_status": likely_status,
                "blocker_category": category,
                "blocker_reason": blocker,
                "recommended_repair_action": action,
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return rows


def build_repair_rows(
    previous_rows: list[dict[str, str]],
    gate_a_index: dict[tuple[str, str, str], dict[str, str]],
    current_index: dict[tuple[str, str], list[dict[str, str]]],
    diagnostic_index: dict[tuple[str, str], list[dict[str, str]]],
    diagnostic_name_index: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    rows = []
    for row in previous_rows:
        key = draft_key(row)
        gate_a = gate_a_for_row(row, gate_a_index)
        current_matches = current_index.get(key, [])
        diagnostic_matches = diagnostic_index.get(key, [])
        older_matches = [
            match
            for match in diagnostic_matches
            if to_int(match["season"]) is not None
            and to_int(match["season"]) < min(CURRENT_DRAFT_YEARS)
        ]
        name_matches = diagnostic_name_index.get(normalize_identity_name(row["player_name"]), [])
        if current_matches:
            match = current_matches[0]
            draft_round = clean(match["round"])
            draft_pick = clean(match["pick"])
            season = clean(match["season"])
            drafted_team = normalize_team(clean(match["team"]))
            status = "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE"
            source = f"nflverse_draft_picks_{season}"
            provenance = (
                f"nflreadpy.load_draft_picks({list(CURRENT_DRAFT_YEARS)}) exact "
                "normalized-name + position match; review-only, not source truth."
            )
            action = (
                "expanded_draft_year_window_exact_name_position"
                if row["draft_capital_status"].startswith("MISSING")
                else "preserved_exact_name_position_match"
            )
            confidence = "HIGH_REVIEW_ONLY"
            quality = "PARTIAL_DRAFT_CAPITAL_COVERAGE_REPAIR_V2_AVAILABLE"
            udfa_status = "not_udfa_drafted"
            udfa_source = source
            bucket = draft_capital_bucket_v2({"draft_round": draft_round})
        elif older_matches:
            match = older_matches[0]
            draft_round = draft_pick = drafted_team = season = NOT_ENOUGH
            status = "BLOCKED_WRONG_UNIVERSE_OLDER_NFL_DRAFT_MATCH"
            source = NOT_ENOUGH
            provenance = (
                "Exact name + position matched older nflverse draft pick "
                f"{match['season']} round {match['round']} pick {match['pick']}; "
                "not repaired as current rookie draft capital."
            )
            action = "block_wrong_universe_or_identity_review_required"
            confidence = "BLOCKED"
            quality = "BLOCKED_CURRENT_ROOKIE_UNIVERSE_REVIEW_REQUIRED"
            udfa_status = "unknown"
            udfa_source = "older_nfl_draft_match"
            bucket = NOT_ENOUGH
        else:
            draft_round = draft_pick = drafted_team = season = NOT_ENOUGH
            status = "MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED"
            source = NOT_ENOUGH
            provenance = (
                "No exact normalized-name + position match in admitted nflverse "
                "2025/2026 draft_picks."
            )
            action = repair_action_for_unmatched(row, gate_a, name_matches)
            confidence = "UNKNOWN"
            quality = "MISSING_AFTER_DRAFT_CAPITAL_REPAIR_V2"
            udfa_status = likely_udfa_status(row, gate_a, False, False)
            udfa_source = udfa_source_for_status(udfa_status)
            bucket = (
                "udfa_review_needed"
                if udfa_status == "likely_udfa_needs_review"
                else NOT_ENOUGH
            )
        rows.append(
            {
                "player_id": clean(row["player_id"]),
                "player_name": clean(row["player_name"]),
                "position": clean(row["position"]),
                "team": drafted_team if current_matches else gate_a_team(gate_a),
                "rookie_class_year": season,
                "draft_year": season,
                "draft_round": draft_round,
                "draft_pick": draft_pick,
                "overall_pick": draft_pick,
                "drafted_team": drafted_team,
                "draft_capital_bucket": bucket,
                "draft_capital_source": source,
                "draft_capital_provenance": provenance,
                "draft_capital_status": status,
                "udffa_or_undrafted_status": udfa_status,
                "udffa_or_undrafted_source": udfa_source,
                "repair_action": action,
                "repair_confidence": confidence,
                "data_quality_status": quality,
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return rows


def build_feature_policy_rows() -> list[dict[str, str]]:
    rows = []
    for feature in (
        "draft_round",
        "draft_pick",
        "overall_pick",
        "draft_capital_bucket",
        "rookie_class_year",
        "position",
    ):
        rows.append(
            feature_row(
                "draft_capital",
                feature,
                "nflverse draft_picks / repair v2 review artifact",
                "available_partial",
                "allowed_review_only_model_rd",
                "true",
                "true",
                "low",
                "partial_current_rookie_coverage",
                NOT_ENOUGH,
                "Gate E refresh if future prompt approves.",
                "Factual completed draft field; still review-only.",
            )
        )
    rows.extend(
        [
            feature_row(
                "draft_capital",
                "draft_capital_value",
                NOT_ENOUGH,
                "missing",
                "blocked",
                "false",
                "false",
                "low",
                "missing",
                "No approved non-linear draft value table in this lane.",
                "Draft-value source policy lane.",
                "Do not derive opaque values.",
            ),
            feature_row(
                "draft_context",
                "UDFA_status",
                "nflverse draft_picks absence + NWR/Sleeper team context",
                "review_needed_partial",
                "review_only_context",
                "false",
                "true",
                "medium",
                "high",
                "Absence from draft_picks is not enough to confirm UDFA.",
                "UDFA/free-agent source approval lane.",
                "Likely UDFA rows remain display-blocked until approved.",
            ),
            feature_row(
                "blocked_or_unchanged",
                "college_production_combine_grades_market_cfbd",
                "unchanged from previous gates",
                "unchanged",
                "blocked_or_display_context_only",
                "false",
                "false",
                "high",
                "high",
                "Out of scope for draft-capital-only V2 lane.",
                "Separate source-policy and validation lanes.",
                "No policy expansion outside draft capital fields.",
            ),
        ]
    )
    return rows


def build_display_rows(
    repair_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    gate_e_summary: list[dict[str, str]],
    gate_e_metrics: list[dict[str, str]],
) -> list[dict[str, str]]:
    model_status = {row["metric"]: row["value"] for row in gate_e_summary}["gate_e_verdict"]
    metric_status = {row["target_name"]: row["validation_status"] for row in gate_e_metrics}
    rate_tables = {target: build_rate_table(label_rows, target) for target in TARGETS}
    output = []
    for repair_row in repair_rows:
        row = base_display_row(repair_row, model_status)
        methods: Counter[str] = Counter()
        display_count = 0
        nei_count = 0
        for target in TARGETS:
            column = target_to_display_column(target)
            if not has_display_features(row):
                row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            if not target_is_supported_for_position(target, row["position"]):
                row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            if metric_status.get(target) != "pass_review_only":
                row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            rate, method = display_rate_for_row(row, rate_tables[target])
            row[column] = rate
            methods[method] += 1
            display_count += 1
        row["display_field_count"] = str(display_count)
        row["not_enough_information_field_count"] = str(nei_count)
        row["rate_method_summary"] = format_counts(methods) if methods else NOT_ENOUGH
        if display_count:
            row["feature_coverage_status"] = "complete_allowed_drafted_features"
            row["validation_status"] = "gate_e_v1_pass_review_only_preserved"
            row["display_status"] = "review_only_display_fields_available"
            row["data_quality_status"] = "PARTIAL_REVIEW_ONLY_DISPLAY_V3_AVAILABLE"
            row["notes"] = "Drafted-player review-only display rates; not app-wired."
        output.append(row)
    return output


def base_display_row(source_row: dict[str, str], model_status: str) -> dict[str, str]:
    row = {
        "player_id": source_row["player_id"],
        "player_name": source_row["player_name"],
        "position": source_row["position"],
        "team": source_row["team"],
        "rookie_class_year": source_row["rookie_class_year"],
        "draft_year": source_row["draft_year"],
        "draft_round": source_row["draft_round"],
        "draft_pick": source_row["draft_pick"],
        "overall_pick": source_row["overall_pick"],
        "draft_capital_bucket": source_row["draft_capital_bucket"],
        "udffa_or_undrafted_status": source_row["udffa_or_undrafted_status"],
        "identity_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
        "draft_capital_status": source_row["draft_capital_status"],
        "feature_coverage_status": NOT_ENOUGH,
        "model_rd_status": model_status,
        "validation_status": NOT_ENOUGH,
        "display_status": NOT_ENOUGH,
        "data_quality_status": source_row["data_quality_status"],
        "source_provenance_status": source_row["draft_capital_provenance"],
        "repair_action": source_row["repair_action"],
        "repair_confidence": source_row["repair_confidence"],
        "display_field_count": "0",
        "not_enough_information_field_count": str(len(TARGETS)),
        "rate_method_summary": NOT_ENOUGH,
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
        "notes": (
            "Missing approved drafted-player features; display values remain "
            "Not enough information."
        ),
    }
    for target in TARGETS:
        row[target_to_display_column(target)] = NOT_ENOUGH
    return row


def build_rate_table(rows: list[dict[str, str]], target: str) -> dict[str, object]:
    eligible = eligible_rows(rows, target)
    global_rate = sum(target_value(row[target]) for row in eligible) / len(eligible)
    by_position_bucket: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_position: dict[str, list[int]] = defaultdict(list)
    for row in eligible:
        actual = target_value(row[target])
        bucket = draft_capital_bucket_v2(row)
        if bucket == NOT_ENOUGH:
            continue
        by_position_bucket[(row["position"], bucket)].append(actual)
        by_position[row["position"]].append(actual)
    return {
        "global_rate": global_rate,
        "by_position_bucket": by_position_bucket,
        "by_position": by_position,
    }


def display_rate_for_row(row: dict[str, str], rate_table: dict[str, object]) -> tuple[str, str]:
    global_rate = rate_table["global_rate"]
    by_position_bucket = rate_table["by_position_bucket"]
    by_position = rate_table["by_position"]
    grouped = by_position_bucket[(row["position"], row["draft_capital_bucket"])]
    if len(grouped) >= 5:
        return format_rate(smoothed_rate(grouped, global_rate)), "position_draft_capital_bucket"
    position_group = by_position[row["position"]]
    if len(position_group) >= 10:
        return format_rate(smoothed_rate(position_group, global_rate)), "position"
    return format_rate(global_rate), "global"


def eligible_rows(rows: list[dict[str, str]], target: str) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if target.startswith("first_3y") and row["first_3y_window_complete"] != "true":
            continue
        if target.startswith("first_5y") and row["first_5y_window_complete"] != "true":
            continue
        if target_value(row.get(target)) is None:
            continue
        output.append(row)
    return output


def write_docs(
    root: Path,
    previous_repair_rows: list[dict[str, str]],
    previous_display_rows: list[dict[str, str]],
    gate_e_metrics: list[dict[str, str]],
    source_registry_rows: list[dict[str, str]],
    current_draft_picks: list[dict[str, str]],
    diagnosis_rows: list[dict[str, str]],
    repair_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
) -> None:
    diagnosis_counts = Counter(row["blocker_category"] for row in diagnosis_rows)
    udfa_counts = Counter(row["udffa_or_undrafted_status"] for row in repair_rows)
    source_keys = {
        (row["source_name"], row["source_table"]): row["default_admissibility"]
        for row in source_registry_rows
    }
    write_doc(
        root / "00_COVERAGE_REPAIR_INVENTORY.md",
        [
            "# Gate 0 Coverage Repair Inventory - 2026-06-30",
            "",
            f"- Actual base HEAD: `{BASE_HEAD}`",
            f"- Current Gate F V2 display rows: {len(previous_display_rows)}",
            f"- Current draft-capital repair rows: {len(previous_repair_rows)}",
            f"- Current 157-row universe: {len(previous_repair_rows)}",
            f"- Current valid display rows: {count_display_rows(previous_display_rows)}",
            (
                "- Current `Not enough information` rows: "
                f"{count_not_enough_rows(previous_display_rows)}"
            ),
            (
                "- Source registry: nflverse draft_picks="
                f"{source_keys.get(('nflverse', 'draft_picks'), 'missing')}; "
                f"combine={source_keys.get(('nflverse', 'combine'), 'missing')}; "
                "nflverse players/rosters are not explicit draft-capital sources here."
            ),
            (
                "- JackLich10, array-carpenter, ESPN/NFL grades, and FootballDB remain "
                "blocked per the prior source-intake matrix."
            ),
            (
                "- Current feature policy allows draft_round, draft_pick, overall_pick, "
                "draft_capital_bucket, draft_year/rookie_class_year, and position only."
            ),
            f"- Gate E validation targets preserved: {len(gate_e_metrics)}",
            "",
            "Inventory is complete; no app/rank/model files are touched.",
        ],
    )
    write_doc(
        root / "01_MISSINGNESS_DIAGNOSIS.md",
        [
            "# Gate 1 Missingness Diagnosis - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`GREEN_MISSINGNESS_DIAGNOSIS_REVIEW_ONLY`",
            "",
            f"- Missing Gate F V2 rows diagnosed: {len(diagnosis_rows)}",
            f"- Drafted join misses: {diagnosis_counts['drafted_join_miss']}",
            (
                "- Likely UDFA / undrafted needs source rows: "
                f"{diagnosis_counts['likely_udfa_needs_source']}"
            ),
            (
                "- Wrong-universe older NFL draft matches: "
                f"{diagnosis_counts['not_draft_eligible_or_wrong_universe']}"
            ),
            f"- Needs human review / unknown: {diagnosis_counts['needs_human_review']}",
            "",
            (
                "Diagnosis uses only admitted nflverse draft-pick facts plus existing "
                "review-only NWR/CFBD identity context."
            ),
        ],
    )
    write_doc(
        root / "02_SOURCE_SAFE_REPAIR_RESULT.md",
        [
            "# Gate 2 Source-Safe Repair Result - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_DRAFT_CAPITAL_COVERAGE_REPAIR_V2`",
            "",
            f"- nflverse current-window draft-pick rows loaded: {len(current_draft_picks)}",
            (
                "- Repair method: exact normalized player name + position across "
                "2025 and 2026 draft picks."
            ),
            "- Previous drafted display-capable rows: 62",
            f"- New drafted display-capable rows: {count_available_drafted_rows(repair_rows)}",
            f"- New repairs from the 95 missing rows: {count_new_repairs(repair_rows)}",
            (
                "- Rows still not display-capable: "
                f"{len(repair_rows) - count_available_drafted_rows(repair_rows)}"
            ),
            (
                "- No JackLich10, array-carpenter, FootballDB, grades, market, "
                "or vendor sources were used."
            ),
        ],
    )
    write_doc(
        root / "03_DRAFT_CAPITAL_BUCKET_POLICY_V2.md",
        [
            "# Gate 3 Draft-Capital Bucket Policy V2 - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`GREEN_DRAFT_CAPITAL_BUCKET_POLICY_V2`",
            "",
            (
                "- Modern NFL draft buckets: `round_1`, `round_2`, `round_3`, "
                "`round_4`, `round_5`, `round_6`, `round_7`."
            ),
            "- `udfa_review_needed` is separate from draft rounds and is not a fake round.",
            "- `Not enough information` remains the value for unknown or blocked rows.",
            "- Round 8 is not a normal current-rookie draft-capital bucket.",
            "- Current rookies must not use round 8 as a proxy for UDFA.",
            (
                "- `draft_capital_value` remains blocked because no approved value "
                "table exists in this lane."
            ),
        ],
    )
    allowed = [
        row["feature_name"]
        for row in feature_rows
        if row["allowed_for_review_only_model_rd"] == "true"
    ]
    write_doc(
        root / "04_FEATURE_POLICY_REFRESH_DRAFT_CAPITAL_V2.md",
        [
            "# Gate 4 Feature Policy Refresh Draft Capital V2 - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_DRAFT_CAPITAL_FEATURE_POLICY_V2`",
            "",
            f"- Allowed review-only R&D draft-capital fields: {', '.join(allowed)}",
            "- UDFA status is review/display context only and remains blocked as model input.",
            "- Draft capital value remains blocked.",
            (
                "- College production, combine, grades, market, and CFBD production "
                "policies are unchanged."
            ),
        ],
    )
    write_doc(
        root / "05_GATE_G_RELEASE_AUDIT_AFTER_REPAIR_V2.md",
        [
            "# Gate 6 Gate G Release Audit After Repair V2 - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`BLOCKED_NEEDS_DISPLAY_COVERAGE`",
            "",
            "- Gate F V3 improves coverage but remains partial.",
            "- Rankings wiring approval was not granted in this lane.",
            "- No app code was touched.",
            "- Gate G should not run next.",
        ],
    )
    write_doc(
        root / "06_GATE_F_V3_DISPLAY_REBUILD_RESULT.md",
        [
            "# Gate 5 Gate F V3 Display Artifact Rebuild - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_DISPLAY_ARTIFACT_V3_COVERAGE_REPAIR`",
            "",
            "- Previous valid display rows: 62",
            "- Previous `Not enough information` rows: 95",
            f"- New valid display rows: {count_display_rows(display_rows)}",
            f"- New `Not enough information` rows: {count_not_enough_rows(display_rows)}",
            f"- Confirmed UDFA rows: {udfa_counts['confirmed_udfa']}",
            f"- Likely UDFA / undrafted review rows: {udfa_counts['likely_udfa_needs_review']}",
            (
                "- Rows still blocked or requiring human review: "
                f"{count_not_enough_rows(display_rows)}"
            ),
            (
                "- Shared V3 display outputs were written outside git under "
                "`C:\\NWR_SHARED_DATA\\rookie_outcomes\\display_artifact_v3\\`."
            ),
        ],
    )
    write_doc(
        root / "README.md",
        [
            "# Rookie Draft-Capital Coverage Repair V2",
            "",
            "This package repairs review-only current-rookie draft-capital coverage using",
            "admitted nflverse draft-pick facts. It does not create probabilities, wire",
            "Rankings, promote source truth, scrape blocked sources, or treat UDFA absence",
            "as confirmed draft capital.",
        ],
    )


def build_display_summary_rows(display_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    values = {
        "gate_f_v3_verdict": (
            "PARTIAL_DISPLAY_ARTIFACT_V3_COVERAGE_REPAIR",
            "Coverage improved but remains partial.",
        ),
        "previous_valid_display_rows": ("62", "Gate F V2 valid display rows."),
        "new_valid_display_rows": (
            str(count_display_rows(display_rows)),
            "Gate F V3 valid display rows.",
        ),
        "previous_not_enough_information_rows": ("95", "Gate F V2 Not enough information rows."),
        "new_not_enough_information_rows": (
            str(count_not_enough_rows(display_rows)),
            "Gate F V3 Not enough information rows.",
        ),
        "rankings_wiring_allowed": ("false", "Gate G remains blocked."),
    }
    return [summary_row(metric, value, notes) for metric, (value, notes) in values.items()]


def build_gate_a_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    index = {}
    for row in rows:
        if row.get("gate_a_status") != "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL":
            continue
        keys = [
            (
                clean(row.get("player_id")),
                normalize_identity_name(row.get("player_name", "")),
                clean(row.get("position")).upper(),
            ),
            (
                NOT_ENOUGH,
                normalize_identity_name(row.get("player_name", "")),
                clean(row.get("position")).upper(),
            ),
        ]
        for key in keys:
            index.setdefault(key, row)
    return index


def gate_a_for_row(
    row: dict[str, str],
    gate_a_index: dict[tuple[str, str, str], dict[str, str]],
) -> dict[str, str]:
    exact_key = (
        clean(row.get("player_id")),
        normalize_identity_name(row.get("player_name", "")),
        clean(row.get("position")).upper(),
    )
    fallback_key = (
        NOT_ENOUGH,
        normalize_identity_name(row.get("player_name", "")),
        clean(row.get("position")).upper(),
    )
    return gate_a_index.get(exact_key) or gate_a_index.get(fallback_key) or {}


def build_draft_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        position = clean(row.get("position")).upper()
        if position not in SKILL_POSITIONS:
            continue
        name = normalize_identity_name(clean(row.get("pfr_player_name")))
        if not name:
            continue
        index[(name, position)].append(row)
    return index


def build_name_index(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        name = normalize_identity_name(clean(row.get("pfr_player_name")))
        if name:
            index[name].append(row)
    return index


def draft_key(row: dict[str, str]) -> tuple[str, str]:
    return (
        normalize_identity_name(clean(row.get("player_name"))),
        clean(row.get("position")).upper(),
    )


def likely_udfa_status(
    row: dict[str, str],
    gate_a: dict[str, str],
    has_current_match: bool,
    has_older_match: bool,
) -> str:
    if has_current_match:
        return "not_udfa_drafted"
    if has_older_match:
        return "unknown"
    team = gate_a_team(gate_a)
    cfbd_years = clean(gate_a.get("cfbd_years"))
    if team not in {NOT_ENOUGH, "NEEDS_DATA"} and cfbd_years != NOT_ENOUGH:
        return "likely_udfa_needs_review"
    if team == "NEEDS_DATA" and cfbd_years != NOT_ENOUGH:
        return "not_in_draft_picks_needs_review"
    return "unknown"


def repair_action_for_unmatched(
    row: dict[str, str],
    gate_a: dict[str, str],
    name_matches: list[dict[str, str]],
) -> str:
    if name_matches:
        return "block_position_mismatch_or_identity_review_required"
    if likely_udfa_status(row, gate_a, False, False) == "likely_udfa_needs_review":
        return "label_likely_udfa_review_needed_without_display_rates"
    return "leave_as_not_enough_information"


def udfa_source_for_status(status: str) -> str:
    if status == "not_udfa_drafted":
        return "nflverse_draft_picks_match"
    if status == "likely_udfa_needs_review":
        return "not_in_2025_2026_nflverse_draft_picks_plus_review_only_nwr_team_context"
    if status == "not_in_draft_picks_needs_review":
        return "not_in_2025_2026_nflverse_draft_picks"
    return NOT_ENOUGH


def gate_a_team(gate_a: dict[str, str]) -> str:
    team = clean(gate_a.get("nfl_team_if_available"))
    if team == "FA":
        return "FA"
    return team


def team_or_school_status(
    gate_a: dict[str, str],
    current_matches: list[dict[str, str]],
) -> str:
    if current_matches:
        return f"drafted_team={normalize_team(clean(current_matches[0]['team']))}"
    team = gate_a_team(gate_a)
    school = clean(gate_a.get("college_team"))
    if team != NOT_ENOUGH:
        return f"review_only_nwr_team_context={team}"
    if school != NOT_ENOUGH:
        return f"review_only_cfbd_school_context={school}"
    return NOT_ENOUGH


def format_candidates(matches: list[dict[str, str]]) -> str:
    if not matches:
        return NOT_ENOUGH
    parts = []
    for match in matches[:5]:
        parts.append(
            "|".join(
                (
                    clean(match.get("pfr_player_name")),
                    clean(match.get("position")),
                    clean(match.get("season")),
                    f"round={clean(match.get('round'))}",
                    f"pick={clean(match.get('pick'))}",
                    f"team={normalize_team(clean(match.get('team')))}",
                )
            )
        )
    return "; ".join(parts)


def feature_row(
    family: str,
    name: str,
    source: str,
    availability: str,
    approval: str,
    model_rd: str,
    display: str,
    leakage: str,
    missingness: str,
    blocker: str,
    next_gate: str,
    notes: str,
) -> dict[str, str]:
    return {
        "feature_family": family,
        "feature_name": name,
        "source": source,
        "availability_status": availability,
        "approval_status": approval,
        "allowed_for_review_only_model_rd": model_rd,
        "allowed_for_display_context": display,
        "model_use_allowed": "false",
        "training_allowed": "false",
        "review_only": "true",
        "leakage_risk": leakage,
        "missingness_risk": missingness,
        "blocker_reason": blocker,
        "required_next_gate": next_gate,
        "notes": notes,
    }


def has_display_features(row: dict[str, str]) -> bool:
    return (
        row["draft_capital_status"] == "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE"
        and row["udffa_or_undrafted_status"] == "not_udfa_drafted"
        and all(
            row[field] != NOT_ENOUGH
            for field in (
                "position",
                "draft_year",
                "rookie_class_year",
                "draft_round",
                "draft_pick",
                "overall_pick",
                "draft_capital_bucket",
            )
        )
    )


def draft_capital_bucket_v2(row: dict[str, str]) -> str:
    draft_round = to_int(row.get("draft_round"))
    if draft_round is None:
        return NOT_ENOUGH
    if 1 <= draft_round <= 7:
        return f"round_{draft_round}"
    return NOT_ENOUGH


def target_value(label: object) -> int | None:
    value = str(label or "").strip()
    if value == "hit":
        return 1
    if value == "miss":
        return 0
    return None


def target_is_supported_for_position(target: str, position: str) -> bool:
    threshold = int(target.rsplit("_top_", 1)[1].split("_", 1)[0])
    return threshold in POSITION_SUPPORTED_THRESHOLDS.get(position, set())


def target_to_display_column(target: str) -> str:
    return target.replace("_hit", "_review_display_rate")


def shared_manifest_rows(name: str, rows: int) -> list[dict[str, str]]:
    return [
        summary_row("run_id", RUN_ID, name),
        summary_row("run_timestamp", datetime.now(UTC).replace(microsecond=0).isoformat(), name),
        summary_row("artifact_rows", str(rows), name),
    ]


def summary_row(metric: str, value: str, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": value,
        "notes": notes,
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
    }


def count_available_drafted_rows(rows: list[dict[str, str]]) -> int:
    return sum(
        row["draft_capital_status"] == "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE"
        for row in rows
    )


def count_new_repairs(rows: list[dict[str, str]]) -> int:
    return sum(
        row["repair_action"] == "expanded_draft_year_window_exact_name_position"
        for row in rows
    )


def count_display_rows(rows: list[dict[str, str]]) -> int:
    return sum(int(row["display_field_count"]) > 0 for row in rows)


def count_not_enough_rows(rows: list[dict[str, str]]) -> int:
    return sum(row["display_status"] == NOT_ENOUGH for row in rows)


def count_udfa_status(rows: list[dict[str, str]], status: str) -> int:
    return sum(row["udffa_or_undrafted_status"] == status for row in rows)


def clean(value: object) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "<na>"} or not text:
        return NOT_ENOUGH
    return text


def normalize_team(team: str) -> str:
    mapping = {"NOR": "NO", "SFO": "SF", "KAN": "KC", "GNB": "GB", "LVR": "LV"}
    return mapping.get(team, team)


def to_int(value: object) -> int | None:
    text = clean(value)
    if text == NOT_ENOUGH:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def smoothed_rate(values: list[int], global_rate: float, alpha: int = 5) -> float:
    return (sum(values) + global_rate * alpha) / (len(values) + alpha)


def format_rate(value: float) -> str:
    return f"{value:.6f}"


def format_counts(counter: Counter[str]) -> str:
    if not counter:
        return NOT_ENOUGH
    return "; ".join(f"{key}:{counter[key]}" for key in sorted(counter))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def write_doc(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_nflverse_draft_picks(seasons: tuple[int, ...]) -> list[dict[str, str]]:
    import nflreadpy  # noqa: PLC0415

    data = nflreadpy.load_draft_picks(list(seasons))
    if hasattr(data, "to_pandas"):
        frame = data.to_pandas()
        return [
            {column: clean(row[column]) for column in frame.columns}
            for _, row in frame.iterrows()
        ]
    if hasattr(data, "to_dicts"):
        return [
            {column: clean(value) for column, value in row.items()}
            for row in data.to_dicts()
        ]
    return [
        {column: clean(value) for column, value in row.items()}
        for row in data.to_dict("records")
    ]


if __name__ == "__main__":
    main()
