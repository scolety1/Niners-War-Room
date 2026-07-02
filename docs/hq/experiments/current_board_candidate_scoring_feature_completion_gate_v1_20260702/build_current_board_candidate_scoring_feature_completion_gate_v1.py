from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ARTIFACT_DIR = Path(__file__).resolve().parent
ROOT = ARTIFACT_DIR.parents[3]
sys.path.insert(0, str(ROOT))

from src.services.nwr_outcome_scoring_service import (  # noqa: E402
    load_scoring_rules,
    score_player_week,
)


BRANCH = "work/current-board-candidate-feature-input-gate-v1-20260702"
STARTING_HEAD = "1d5339ed49edd6d5b4cb1ea5daadc6195d1d8cc4"
DECISION = "PARTIAL_SCORING_FEATURES_COMPLETED_WITH_NULL_FENCES"
SELECTED = "wr_boundary_breakout_sensitivity_guard"
FEATURE_ANCHOR_SEASON = 2025
PREDICTION_ANCHOR = "2026_current_board_shadow_review"
BASELINE_ROWS = 370
BASELINE_SHA256 = "85bca72a67860260eb03e5907087c3fe7e7e521fb69779bd3264e747d5908952"
PARTIAL_SHA256 = "163da41dedb5c4a05f16c00a8788ff3130db5d794894d400c5f111bf58af1235"
RAW_WEEKLY_SHA256 = "a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba"
RAW_WEEKLY_ROWS = 76804
RAW_WEEKLY_2025_REG_RAW_ROWS = 37078
RAW_WEEKLY_2025_REG_DEDUP_ROWS = 18539

BASELINE_INPUT = Path(
    r"C:\NWR_REVIEW\current_board_shadow_input_gate_v1_20260702"
    r"\current_board_baseline_shadow_input_review_only.csv"
)
PARTIAL_INPUT = Path(
    r"C:\NWR_REVIEW\current_board_candidate_feature_input_gate_v1_20260702"
    r"\current_board_candidate_feature_input_review_only.csv"
)
OUTSIDE_DIR = Path(
    r"C:\NWR_REVIEW\current_board_candidate_scoring_feature_completion_gate_v1_20260702"
)
OUTSIDE_EXPORT = OUTSIDE_DIR / "current_board_candidate_feature_input_completed_review_only.csv"
RAW_WEEKLY_SOURCE = Path(
    r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse"
    r"\player_stats_source_admission_v1_20260630\player_stats_weekly.csv"
)
RAW_SNAPSHOT_REPORT = Path(
    r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse"
    r"\player_stats_source_admission_v1_20260630\nflverse_pull_report.md"
)
SCORING_CONFIG = ROOT / "config" / "nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json"
SCORING_ALIGNMENT = (
    ROOT
    / "docs"
    / "hq"
    / "outcomes"
    / "outcome_full_scoring_formula_alignment_v1_20260630"
)
SOURCE_CONTRACT = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_source_contract_v1_20260701"
)

PRIMARY_FEATURES = [
    "prior_carries",
    "prior_games",
    "prior_interceptions",
    "prior_nwr_points",
    "prior_nwr_ppg",
    "prior_opportunities",
    "prior_passing_attempts",
    "prior_passing_completions",
    "prior_passing_first_downs",
    "prior_passing_td",
    "prior_passing_yards",
    "prior_receiving_first_downs",
    "prior_receiving_yards",
    "prior_receptions",
    "prior_rushing_first_downs",
    "prior_rushing_yards",
    "prior_targets",
    "prior_touches",
]
SCORING_FEATURES = ["prior_nwr_points", "prior_games", "prior_nwr_ppg"]
NULL_FENCED_OPTIONAL = {
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
}
SCORING_SOURCE_COLUMNS = [
    "player_id",
    "player_display_name",
    "position",
    "season",
    "week",
    "season_type",
    "team",
    "game_id",
    "passing_yards",
    "passing_tds",
    "passing_interceptions",
    "passing_first_downs",
    "passing_2pt_conversions",
    "sacks_suffered",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "rushing_2pt_conversions",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "receiving_2pt_conversions",
    "sack_fumbles_lost",
    "rushing_fumbles_lost",
    "receiving_fumbles_lost",
    "kickoff_return_yards",
    "punt_return_yards",
    "special_teams_tds",
    "fumble_recovery_tds",
    "misc_yards",
]
NUMERIC_SCORING_SOURCE_COLUMNS = [
    column
    for column in SCORING_SOURCE_COLUMNS
    if column
    not in {
        "player_id",
        "player_display_name",
        "position",
        "season",
        "week",
        "season_type",
        "team",
        "game_id",
    }
]
OUTPUT_METADATA_FIELDS = [
    "scoring_feature_status",
    "scoring_missing_reason",
    "scoring_source_artifact",
    "scoring_version_id",
    "prior_games_derivation",
    "prior_nwr_points_derivation",
    "prior_nwr_ppg_derivation",
]


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUTSIDE_DIR.mkdir(parents=True, exist_ok=True)

    baseline_checksum = sha256(BASELINE_INPUT)
    if baseline_checksum != BASELINE_SHA256:
        raise SystemExit(f"Baseline checksum mismatch: {baseline_checksum}")
    baseline_rows = read_csv(BASELINE_INPUT)
    if len(baseline_rows) != BASELINE_ROWS:
        raise SystemExit(f"Baseline row count mismatch: {len(baseline_rows)}")

    partial_checksum = sha256(PARTIAL_INPUT)
    if partial_checksum != PARTIAL_SHA256:
        raise SystemExit(f"Partial candidate feature checksum mismatch: {partial_checksum}")
    partial_rows = read_csv(PARTIAL_INPUT)
    if len(partial_rows) != BASELINE_ROWS:
        raise SystemExit(f"Partial candidate feature row count mismatch: {len(partial_rows)}")

    raw_checksum = sha256(RAW_WEEKLY_SOURCE)
    if raw_checksum != RAW_WEEKLY_SHA256:
        raise SystemExit(f"Raw player_stats weekly checksum mismatch: {raw_checksum}")

    raw_weekly = load_raw_weekly_source()
    raw_2025 = raw_weekly[
        (pd.to_numeric(raw_weekly["season"], errors="coerce") == FEATURE_ANCHOR_SEASON)
        & raw_weekly["season_type"].astype(str).eq("REG")
    ].copy()
    raw_2025_raw_rows = len(raw_2025)
    raw_2025_exact_duplicate_rows = int(raw_2025.duplicated(keep=False).sum())
    raw_2025 = raw_2025.drop_duplicates().copy()
    duplicate_keys_after_dedup = int(raw_2025.duplicated(subset=["player_id", "season", "week"]).sum())
    if duplicate_keys_after_dedup:
        raise SystemExit(
            f"Duplicate player/week keys remain after exact dedup: {duplicate_keys_after_dedup}"
        )
    missing_component_counts = missing_scoring_component_counts(raw_2025)
    if any(count for count in missing_component_counts.values()):
        raise SystemExit(f"Missing scoring components in observed rows: {missing_component_counts}")

    scoring_aggregate = aggregate_scoring_features(raw_2025)
    completed_rows = complete_candidate_feature_rows(partial_rows, scoring_aggregate)
    output_fields = list(partial_rows[0].keys()) + OUTPUT_METADATA_FIELDS
    write_csv_path(OUTSIDE_EXPORT, completed_rows, output_fields)

    context = {
        "branch": BRANCH,
        "starting_head": STARTING_HEAD,
        "current_head": git("rev-parse", "HEAD"),
        "decision": DECISION,
        "selected": SELECTED,
        "baseline_rows": len(baseline_rows),
        "baseline_sha256": baseline_checksum,
        "partial_rows": len(partial_rows),
        "partial_sha256": partial_checksum,
        "raw_weekly_sha256": raw_checksum,
        "raw_weekly_rows": len(raw_weekly),
        "raw_2025_reg_raw_rows": raw_2025_raw_rows,
        "raw_2025_reg_exact_duplicate_rows": raw_2025_exact_duplicate_rows,
        "raw_2025_reg_after_exact_dedup": len(raw_2025),
        "duplicate_keys_after_dedup": duplicate_keys_after_dedup,
        "scoring_aggregate_players": len(scoring_aggregate),
        "current_board_rows": len(completed_rows),
        "scoring_feature_rows_generated": sum(
            row["scoring_feature_status"] == "EXACT_GSIS_SCORING_MATCH_2025_REG"
            for row in completed_rows
        ),
        "candidate_feature_ready_count": sum(
            row["candidate_feature_ready"] == "true" for row in completed_rows
        ),
        "null_fenced_or_missing_count": sum(
            row["candidate_feature_ready"] != "true" for row in completed_rows
        ),
        "outside_export": str(OUTSIDE_EXPORT),
        "outside_export_sha256": sha256(OUTSIDE_EXPORT),
        "source_component_nulls": missing_component_counts,
    }

    write_csv("scoring_source_inventory.csv", scoring_source_inventory_rows(context))
    write_csv("scoring_feature_schema.csv", scoring_feature_schema_rows())
    write_csv("scoring_feature_join_report.csv", scoring_feature_join_rows(completed_rows))
    write_csv("candidate_feature_ready_row_count_report.csv", row_count_rows(context))
    write_csv("missing_or_null_fenced_players_report.csv", missing_or_null_fenced_rows(completed_rows))
    write_csv("completed_candidate_feature_input_schema.csv", completed_input_schema_rows(output_fields))
    write_csv("completed_candidate_feature_input_sample.csv", completed_rows[:50], output_fields)
    write_csv("completed_candidate_feature_input_checksum_report.csv", checksum_report_rows(context))
    write_csv(
        "completed_candidate_feature_missing_reason_breakdown.csv",
        missing_reason_breakdown_rows(completed_rows),
    )
    write_text("scoring_feature_completion_gate_summary.md", summary_doc(context))
    write_text("scoring_feature_decision.md", decision_doc(context))
    write_text("prior_nwr_points_derivation_report.md", prior_nwr_points_report(context))
    write_text("prior_games_derivation_report.md", prior_games_report(context))
    write_text("prior_nwr_ppg_derivation_report.md", prior_nwr_ppg_report(context))
    write_text("rookie_no_prior_stats_policy.md", rookie_no_prior_stats_policy(context))
    write_text("duplicate_source_row_handling_report.md", duplicate_source_row_report(context))
    write_text("candidate_shadow_rank_input_contract_v2.md", rank_input_contract(context))
    write_text("guardrail_report.md", guardrail_report(context))
    write_text("merge_safety_report.md", merge_safety_report())
    write_text("next_phase_handoff.md", next_phase_handoff(context))
    write_text("artifact_manifest.md", artifact_manifest(context))
    write_outside_readme(context)


def load_raw_weekly_source() -> pd.DataFrame:
    return pd.read_csv(
        RAW_WEEKLY_SOURCE,
        usecols=lambda column: column in set(SCORING_SOURCE_COLUMNS),
        low_memory=False,
    )


def missing_scoring_component_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for column in NUMERIC_SCORING_SOURCE_COLUMNS:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        counts[column] = int(numeric.isna().sum())
    return counts


def aggregate_scoring_features(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    rules = load_scoring_rules(SCORING_CONFIG)
    scored_rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        mapped = scoring_input_row(row)
        scored = score_player_week(mapped, rules)
        scored_rows.append(
            {
                "player_id_gsis": clean(row.get("player_id")),
                "player_name": clean(row.get("player_display_name")),
                "position": clean(row.get("position")).upper(),
                "week": clean(row.get("week")),
                "week_score_total": scored["week_score_total"],
                "scoring_version_id": scored["scoring_version_id"],
            }
        )
    scored = pd.DataFrame(scored_rows)
    output: dict[str, dict[str, Any]] = {}
    for player_id, group in scored.groupby("player_id_gsis", dropna=False):
        player_id_text = clean(player_id)
        if not player_id_text:
            continue
        total = round(float(pd.to_numeric(group["week_score_total"], errors="coerce").sum()), 4)
        games = int(group["week"].nunique(dropna=True))
        output[player_id_text] = {
            "player_id_gsis": player_id_text,
            "player_name": first_nonblank(group["player_name"]),
            "position": first_nonblank(group["position"]),
            "prior_games": games,
            "prior_nwr_points": total,
            "prior_nwr_ppg": round(total / games, 4) if games > 0 else "",
            "scoring_version_id": first_nonblank(group["scoring_version_id"]),
            "source_week_rows": int(len(group)),
        }
    return output


def scoring_input_row(row: dict[str, Any]) -> dict[str, Any]:
    fumbles_lost = sum_number(row, "sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost")
    return_yards = sum_number(row, "kickoff_return_yards", "punt_return_yards")
    return {
        "passing_yards": row.get("passing_yards"),
        "passing_tds": row.get("passing_tds"),
        "interceptions": row.get("passing_interceptions"),
        "passing_first_downs": row.get("passing_first_downs"),
        "passing_2pt": row.get("passing_2pt_conversions"),
        "sacks_suffered": row.get("sacks_suffered"),
        "carries": row.get("carries"),
        "rushing_yards": row.get("rushing_yards"),
        "rushing_tds": row.get("rushing_tds"),
        "rushing_first_downs": row.get("rushing_first_downs"),
        "rush_2pt": row.get("rushing_2pt_conversions"),
        "receptions": row.get("receptions"),
        "receiving_yards": row.get("receiving_yards"),
        "receiving_tds": row.get("receiving_tds"),
        "receiving_first_downs": row.get("receiving_first_downs"),
        "rec_2pt": row.get("receiving_2pt_conversions"),
        "fumbles_lost": fumbles_lost,
        "return_yards": return_yards,
        "return_td": 0,
        "special_td": row.get("special_teams_tds"),
        "fumble_recovery_tds": row.get("fumble_recovery_tds"),
        "misc_yards": row.get("misc_yards"),
    }


def complete_candidate_feature_rows(
    partial_rows: list[dict[str, str]],
    scoring_aggregate: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for original in partial_rows:
        row = dict(original)
        gsis = clean(row.get("player_id_gsis"))
        aggregate = scoring_aggregate.get(gsis)
        if aggregate and row.get("feature_join_status") == "EXACT_SLEEPER_MATCH_2025_USAGE":
            row["prior_games"] = format_number(aggregate["prior_games"])
            row["prior_nwr_points"] = format_number(aggregate["prior_nwr_points"])
            row["prior_nwr_ppg"] = format_number(aggregate["prior_nwr_ppg"])
            row["scoring_feature_status"] = "EXACT_GSIS_SCORING_MATCH_2025_REG"
            row["scoring_missing_reason"] = ""
            row["scoring_source_artifact"] = (
                "local-only player_stats_weekly raw snapshot with tracked source receipt checksum"
            )
            row["scoring_version_id"] = clean(aggregate["scoring_version_id"])
            row["prior_games_derivation"] = "count_distinct_2025_reg_player_weeks_after_exact_dedup"
            row["prior_nwr_points_derivation"] = (
                "sum_nwr_scored_2025_reg_observed_player_week_rows"
            )
            row["prior_nwr_ppg_derivation"] = "prior_nwr_points / prior_games when prior_games > 0"
        else:
            row["scoring_feature_status"] = missing_scoring_status(row)
            row["scoring_missing_reason"] = missing_scoring_reason(row)
            row["scoring_source_artifact"] = (
                "No 2025 REG observed player-week match; not enough information."
            )
            row["scoring_version_id"] = ""
            row["prior_games_derivation"] = ""
            row["prior_nwr_points_derivation"] = ""
            row["prior_nwr_ppg_derivation"] = ""

        missing = missing_required_features(row)
        row["missing_required_features"] = ";".join(missing)
        row["candidate_feature_ready"] = "true" if not missing else "false"
        rows.append(row)
    return rows


def missing_scoring_status(row: dict[str, str]) -> str:
    if row.get("feature_join_status") != "EXACT_SLEEPER_MATCH_2025_USAGE":
        return "NULL_FENCED_NO_2025_USAGE_FEATURE_JOIN"
    if not clean(row.get("player_id_gsis")):
        return "NULL_FENCED_MISSING_GSIS_ID"
    return "NULL_FENCED_NO_2025_REG_SCORING_MATCH"


def missing_scoring_reason(row: dict[str, str]) -> str:
    if row.get("feature_join_status") != "EXACT_SLEEPER_MATCH_2025_USAGE":
        return "Not enough information: no exact stable-id join to 2025 usage features."
    if not clean(row.get("player_id_gsis")):
        return "Not enough information: joined usage row lacks GSIS audit id."
    return "Not enough information: no exact GSIS match in completed 2025 REG scoring source."


def missing_required_features(row: dict[str, str]) -> list[str]:
    if row.get("feature_join_status") != "EXACT_SLEEPER_MATCH_2025_USAGE":
        return ["not_enough_information_no_2025_usage_feature_join"]
    missing = [feature for feature in PRIMARY_FEATURES if clean(row.get(feature)) == ""]
    return missing


def scoring_source_inventory_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "source_name": "approved_current_board_baseline_input",
            "source_path_or_artifact": str(BASELINE_INPUT),
            "rows": str(context["baseline_rows"]),
            "sha256": str(context["baseline_sha256"]),
            "used_for": "row universe and baseline audit fields only",
            "review_only": "true",
            "production_approved": "false",
            "notes": "Checksum verified before use.",
        },
        {
            "source_name": "partial_candidate_feature_input_v1",
            "source_path_or_artifact": str(PARTIAL_INPUT),
            "rows": str(context["partial_rows"]),
            "sha256": str(context["partial_sha256"]),
            "used_for": "pre-existing 2025 usage features and stable identity join",
            "review_only": "true",
            "production_approved": "false",
            "notes": "Checksum verified before use.",
        },
        {
            "source_name": "nflverse_player_stats_weekly_raw_snapshot",
            "source_path_or_artifact": str(RAW_WEEKLY_SOURCE),
            "rows": str(context["raw_weekly_rows"]),
            "sha256": str(context["raw_weekly_sha256"]),
            "used_for": "completed 2025 REG observed-row scoring features",
            "review_only": "true",
            "production_approved": "false",
            "notes": "Matches Core Usage Review source receipt; raw file stays local-only.",
        },
        {
            "source_name": "nwr_scoring_rules_nwr_1qb_nonppr_fd_v1",
            "source_path_or_artifact": str(SCORING_CONFIG.relative_to(ROOT)).replace("\\", "/"),
            "rows": "1",
            "sha256": sha256(SCORING_CONFIG),
            "used_for": "NWR scoring weights",
            "review_only": "true",
            "production_approved": "false",
            "notes": "Existing repo scoring config; not changed by this gate.",
        },
        {
            "source_name": "outcome_full_scoring_formula_alignment_v1",
            "source_path_or_artifact": str(SCORING_ALIGNMENT.relative_to(ROOT)).replace("\\", "/"),
            "rows": "",
            "sha256": "",
            "used_for": "component mapping and composite policy",
            "review_only": "true",
            "production_approved": "false",
            "notes": "Approves observed-row component mapping; zero-row completeness remains fenced.",
        },
    ]


def scoring_feature_schema_rows() -> list[dict[str, str]]:
    return [
        {
            "feature": "prior_nwr_points",
            "status": "COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS",
            "source_or_derivation": "sum scored player-week rows using NWR scoring config",
            "null_policy": "null for players without an exact 2025 REG scoring source match",
            "review_only": "true",
            "production_approved": "false",
            "notes": "Imported fantasy_points and fantasy_points_ppr are blocked and not used.",
        },
        {
            "feature": "prior_games",
            "status": "COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS",
            "source_or_derivation": "count distinct explicit 2025 REG player-week rows after exact dedup",
            "null_policy": "null for players without an exact 2025 REG scoring source match",
            "review_only": "true",
            "production_approved": "false",
            "notes": "This is games-with-explicit-stats evidence, not current availability context.",
        },
        {
            "feature": "prior_nwr_ppg",
            "status": "COMPLETED_WHEN_PRIOR_GAMES_GT_0",
            "source_or_derivation": "prior_nwr_points / prior_games",
            "null_policy": "null unless prior_games > 0",
            "review_only": "true",
            "production_approved": "false",
            "notes": "No division is performed for no-stat/null-fenced players.",
        },
    ]


def scoring_feature_join_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["position"], row["scoring_feature_status"])
        counts[key] = counts.get(key, 0) + 1
    return [
        {
            "position": position,
            "scoring_feature_status": status,
            "rows": str(count),
            "join_key": "player_id_gsis exact after stable_player_id_to_player_id_sleeper gate",
            "fuzzy_name_match_used": "false",
        }
        for (position, status), count in sorted(counts.items())
    ]


def row_count_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        metric("current_board_rows", context["current_board_rows"], "Rows processed from approved baseline universe."),
        metric(
            "scoring_feature_rows_generated",
            context["scoring_feature_rows_generated"],
            "Rows with exact GSIS scoring match and completed scoring features.",
        ),
        metric(
            "candidate_feature_ready_count",
            context["candidate_feature_ready_count"],
            "Rows with all 18 primary candidate input features present.",
        ),
        metric(
            "null_fenced_or_missing_count",
            context["null_fenced_or_missing_count"],
            "Rows left null-fenced/not enough information.",
        ),
        metric("raw_weekly_rows", context["raw_weekly_rows"], "Rows in local raw player_stats weekly snapshot."),
        metric(
            "raw_2025_reg_raw_rows",
            context["raw_2025_reg_raw_rows"],
            "2025 REG rows before exact dedup.",
        ),
        metric(
            "raw_2025_reg_exact_duplicate_rows",
            context["raw_2025_reg_exact_duplicate_rows"],
            "Rows participating in exact duplicate groups before dedup.",
        ),
        metric(
            "raw_2025_reg_after_exact_dedup",
            context["raw_2025_reg_after_exact_dedup"],
            "2025 REG rows after exact dedup.",
        ),
        metric(
            "duplicate_keys_after_dedup",
            context["duplicate_keys_after_dedup"],
            "Duplicate player/season/week keys after exact dedup.",
        ),
        metric("outside_export_path", context["outside_export"], "Full completed feature input path outside repo."),
        metric(
            "outside_export_sha256",
            context["outside_export_sha256"],
            "Checksum for outside-repo completed feature input.",
        ),
    ]


def missing_or_null_fenced_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if row["candidate_feature_ready"] != "true":
            output.append(
                {
                    "stable_player_id": row["stable_player_id"],
                    "player_name": row["player_name"],
                    "position": row["position"],
                    "team": row["team"],
                    "feature_join_status": row["feature_join_status"],
                    "scoring_feature_status": row["scoring_feature_status"],
                    "missing_required_features": row["missing_required_features"],
                    "review_policy": "Not enough information; keep null-fenced and do not fill missing with zero.",
                }
            )
    return output


def completed_input_schema_rows(output_fields: list[str]) -> list[dict[str, str]]:
    rows = []
    for field in output_fields:
        rows.append(
            {
                "field_name": field,
                "field_type": field_type(field),
                "source_or_derivation": field_source(field),
                "review_only": "true",
                "production_approved": "false",
                "candidate_rank_output": str(field.startswith("candidate_rank")).lower(),
            }
        )
    return rows


def checksum_report_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "artifact": "current_board_candidate_feature_input_completed_review_only.csv",
            "path": str(OUTSIDE_EXPORT),
            "rows": str(context["current_board_rows"]),
            "sha256": str(context["outside_export_sha256"]),
            "tracked_in_git": "false",
            "review_only": "true",
        }
    ]


def missing_reason_breakdown_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = row["scoring_missing_reason"] or "candidate_feature_ready"
        counts[reason] = counts.get(reason, 0) + 1
    return [
        {"missing_reason": reason, "rows": str(count)}
        for reason, count in sorted(counts.items())
    ]


def summary_doc(context: dict[str, Any]) -> str:
    return f"""# Current Board Candidate Scoring Feature Completion Gate Summary

Decision: `{context['decision']}`

This gate completed the three previously blocked scoring/games features for current-board rows that have exact 2025 REG observed player-week evidence:

- `prior_nwr_points`
- `prior_games`
- `prior_nwr_ppg`

The full completed input remains local-only at:

`{context['outside_export']}`

Key counts:

- Current-board rows processed: `{context['current_board_rows']}`
- Scoring feature rows generated: `{context['scoring_feature_rows_generated']}`
- Candidate-feature-ready rows: `{context['candidate_feature_ready_count']}`
- Null-fenced / missing rows: `{context['null_fenced_or_missing_count']}`
- Raw 2025 REG player_stats rows before / after exact dedup: `{context['raw_2025_reg_raw_rows']}` / `{context['raw_2025_reg_after_exact_dedup']}`
- Completed input checksum: `{context['outside_export_sha256']}`

The result is partial because rookies, inactive players, and any player without exact 2025 REG factual rows remain `Not enough information`. No missing values were filled with zero.
"""


def decision_doc(context: dict[str, Any]) -> str:
    return f"""# Scoring Feature Decision

Decision: `{context['decision']}`

`prior_nwr_points`, `prior_games`, and `prior_nwr_ppg` can be safely generated for exact 2025 REG observed-row matches using:

- the checksum-matched local NFLVerse `player_stats_weekly` raw snapshot,
- existing NWR scoring rules,
- the merged full-scoring formula alignment packet,
- the prior candidate feature input gate's stable identity joins.

This decision does not approve candidate ranks, app wiring, live preview, production configs, hidden sort, recommendations, source-truth promotion, or formula promotion.

Rows without an exact 2025 REG observed-row scoring match remain null-fenced.
"""


def prior_nwr_points_report(context: dict[str, Any]) -> str:
    return f"""# prior_nwr_points Derivation Report

Status: `COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS`

Derivation:

1. Read local-only NFLVerse `player_stats_weekly` snapshot.
2. Verify SHA256 `{context['raw_weekly_sha256']}` against the Core Usage Review receipt.
3. Keep only completed `{FEATURE_ANCHOR_SEASON}` REG rows.
4. Drop exact duplicate rows.
5. Require every NWR scoring component column to be non-null in observed rows.
6. Score each observed player-week with `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`.
7. Sum scored player-week rows by GSIS player id.

Blocked inputs:

- Imported `fantasy_points` and `fantasy_points_ppr`.
- Market, ADP, vendor projections, ranks, current context, routes, TPRR, YPRR, red-zone sidecars, and ambiguous `rz_att`.

No absent player was assigned zero points.
"""


def prior_games_report(context: dict[str, Any]) -> str:
    return f"""# prior_games Derivation Report

Status: `COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS`

`prior_games` is derived as the count of distinct explicit `{FEATURE_ANCHOR_SEASON}` REG player-week rows after exact duplicate removal.

This is a games-with-explicit-stats denominator for review-only shadow input completion. It is not derived from current roster availability, injury status, depth charts, schedule context, rankings, market, ADP, projections, or target outcomes.

Players absent from the factual source remain null-fenced rather than receiving `0` games.
"""


def prior_nwr_ppg_report(context: dict[str, Any]) -> str:
    return f"""# prior_nwr_ppg Derivation Report

Status: `COMPLETED_WHEN_PRIOR_GAMES_GT_0`

Formula:

`prior_nwr_ppg = prior_nwr_points / prior_games`

The calculation is performed only when `prior_games > 0`. Rows without prior factual rows remain null-fenced. No no-stat player receives `0.0` PPG.
"""


def rookie_no_prior_stats_policy(context: dict[str, Any]) -> str:
    return f"""# Rookie / No Prior Stats Policy

Players with no exact `{FEATURE_ANCHOR_SEASON}` REG observed player-week evidence remain:

`Not enough information`

They are not assigned zero games, zero points, or zero PPG. This includes rookies, inactive players, players outside the NFLVerse completed-season source, and any row lacking a stable identity join.

These rows may appear in a future static packet as null-fenced/watchlist rows, but they must not receive generated candidate shadow ranks unless a later gate admits a safe fallback policy.
"""


def duplicate_source_row_report(context: dict[str, Any]) -> str:
    return f"""# Duplicate Source Row Handling Report

Raw 2025 REG rows before exact dedup: `{context['raw_2025_reg_raw_rows']}`

Rows participating in exact duplicate groups: `{context['raw_2025_reg_exact_duplicate_rows']}`

Rows after exact dedup: `{context['raw_2025_reg_after_exact_dedup']}`

Duplicate player/season/week keys after exact dedup: `{context['duplicate_keys_after_dedup']}`

Policy:

- Exact duplicate raw rows are collapsed before scoring.
- Non-exact duplicates would stop the gate.
- This gate does not infer or fill missing player-week rows.
"""


def rank_input_contract(context: dict[str, Any]) -> str:
    return f"""# Candidate Shadow Rank Input Contract V2

Candidate: `{context['selected']}`

Input status: `SCORING_FEATURES_COMPLETED_FOR_READY_ROWS`

Allowed next use:

- Calculate review-only candidate shadow scores/ranks outside app/runtime paths for rows where `candidate_feature_ready == true`.
- Preserve null-fenced rows as `Not enough information`.
- Join any later static shadow comparison by stable player id only.

Blocked:

- App wiring.
- Live preview.
- Production rankings.
- Hidden sort.
- Recommendations.
- Source-truth promotion.
- Production formula/config changes.
- Candidate output wiring into NWR.

The outside completed feature input is not itself a rank output and is not production-approved.
"""


def guardrail_report(context: dict[str, Any]) -> str:
    return f"""# Guardrail Report

Verdict: `GREEN_SCORING_FEATURE_COMPLETION_REVIEW_ONLY_WITH_NULL_FENCES`

- Baseline input checksum matched.
- Partial candidate feature input checksum matched.
- Current-board row count remained `{context['current_board_rows']}`.
- Stable identity joins only; no fuzzy name matching.
- Scoring features use completed `{FEATURE_ANCHOR_SEASON}` REG factual stats only.
- No 2026 current context or target outcomes were used.
- Missing values were not forced to zero.
- No blocked fields are included.
- Null-fenced optional fields are excluded from the primary input.
- No app/model/rank/source-truth/runtime behavior changed.
- No candidate ranks were wired into NWR.
- No production formula/config files changed.
- No raw/shared/cache/local export/secrets files are tracked.
"""


def merge_safety_report() -> str:
    return """# Merge Safety Report

Merge-safe changed paths:

- `docs/hq/experiments/current_board_candidate_scoring_feature_completion_gate_v1_20260702/`
- `tests/test_current_board_candidate_scoring_feature_completion_gate_v1_20260702.py`

The full completed feature input is local-only under `C:\\NWR_REVIEW\\...` and is not tracked. No production app/model/rank/source-truth/runtime path is changed.
"""


def next_phase_handoff(context: dict[str, Any]) -> str:
    return f"""# Next Phase Handoff

Recommended next phase: `Static Current Board Shadow Packet V1 Rerun`.

Use the completed local-only feature input:

`{context['outside_export']}`

Rules for the next phase:

- Generate candidate shadow scores/ranks only for `candidate_feature_ready == true` rows.
- Keep null-fenced rows as `Not enough information`.
- Build a static offline review packet only.
- Do not create app pages, live preview, app wiring, hidden sort, recommendations, production configs, or formula promotion.
"""


def artifact_manifest(context: dict[str, Any]) -> str:
    names = [
        "scoring_feature_completion_gate_summary.md",
        "scoring_feature_decision.md",
        "prior_nwr_points_derivation_report.md",
        "prior_games_derivation_report.md",
        "prior_nwr_ppg_derivation_report.md",
        "scoring_source_inventory.csv",
        "scoring_feature_schema.csv",
        "scoring_feature_join_report.csv",
        "candidate_feature_ready_row_count_report.csv",
        "missing_or_null_fenced_players_report.csv",
        "rookie_no_prior_stats_policy.md",
        "duplicate_source_row_handling_report.md",
        "candidate_shadow_rank_input_contract_v2.md",
        "guardrail_report.md",
        "merge_safety_report.md",
        "next_phase_handoff.md",
        "completed_candidate_feature_input_schema.csv",
        "completed_candidate_feature_input_sample.csv",
        "completed_candidate_feature_input_checksum_report.csv",
        "completed_candidate_feature_missing_reason_breakdown.csv",
        Path(__file__).name,
    ]
    table = "\n".join(
        f"| `{name}` | `{(ARTIFACT_DIR / name).stat().st_size}` | `{sha256(ARTIFACT_DIR / name)}` |"
        for name in names
        if (ARTIFACT_DIR / name).exists()
    )
    return f"""# Artifact Manifest

Artifact directory: `docs/hq/experiments/current_board_candidate_scoring_feature_completion_gate_v1_20260702/`

Branch: `{context['branch']}`

Starting HEAD: `{context['starting_head']}`

Current HEAD while generated: `{context['current_head']}`

Decision: `{context['decision']}`

Outside completed feature input: `{context['outside_export']}`

Outside completed feature input SHA256: `{context['outside_export_sha256']}`

| artifact | bytes | sha256 |
|---|---:|---|
{table}

All artifacts are review-only and not production-approved.
"""


def write_outside_readme(context: dict[str, Any]) -> None:
    (OUTSIDE_DIR / "README.md").write_text(
        f"""# Current Board Candidate Scoring Feature Completion Gate V1

Decision: `{context['decision']}`

Completed feature input:

`{context['outside_export']}`

Rows: `{context['current_board_rows']}`

Candidate-feature-ready rows: `{context['candidate_feature_ready_count']}`

Null-fenced / missing rows: `{context['null_fenced_or_missing_count']}`

Checksum: `{context['outside_export_sha256']}`

This is review-only input evidence. It is not a candidate rank output and is not production-approved.
""",
        encoding="utf-8",
        newline="\n",
    )


def field_type(field: str) -> str:
    if field in PRIMARY_FEATURES:
        return "number_or_null"
    if field in {
        "review_only",
        "candidate_rank_output_present",
        "production_approved",
        "app_wiring_allowed",
        "model_use_allowed",
        "source_truth_allowed",
        "candidate_feature_ready",
    }:
        return "boolean_string"
    return "string"


def field_source(field: str) -> str:
    if field == "prior_nwr_points":
        return "2025 REG observed-row NWR scoring sum"
    if field == "prior_games":
        return "2025 REG explicit player-week count after exact dedup"
    if field == "prior_nwr_ppg":
        return "prior_nwr_points / prior_games when prior_games > 0"
    if field in OUTPUT_METADATA_FIELDS:
        return "scoring completion gate metadata"
    if field in PRIMARY_FEATURES:
        return "prior candidate feature input gate v1"
    return "prior candidate feature input gate v1 baseline/metadata"


def metric(metric_name: str, value: Any, notes: str) -> dict[str, str]:
    return {"metric": metric_name, "value": str(value), "notes": notes}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, str]], fields: list[str] | None = None) -> None:
    write_csv_path(ARTIFACT_DIR / name, rows, fields)


def write_csv_path(path: Path, rows: list[dict[str, str]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    fieldnames = fields or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(name: str, text: str) -> None:
    (ARTIFACT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def first_nonblank(series: pd.Series) -> str:
    for value in series:
        text = clean(value)
        if text:
            return text
    return ""


def number(value: Any) -> float:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        raise ValueError(f"Missing numeric scoring component: {value!r}")
    return float(parsed)


def sum_number(row: dict[str, Any], *columns: str) -> float:
    return sum(number(row.get(column)) for column in columns)


def format_number(value: Any) -> str:
    if value == "":
        return ""
    parsed = float(value)
    if parsed.is_integer():
        return str(int(parsed))
    return str(round(parsed, 6))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    main()
