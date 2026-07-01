# ruff: noqa: E501

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_pre_draft_asof_coverage_builder_v1_20260630"
)

BASE_HEAD = "888c4f13a1b39a24d6b95393508ca759203baa18"
BRANCH = "work/rookie-pre-draft-asof-coverage-builder-v1-20260630"
WORKTREE = r"C:\NWR\Niners-War-Room-rookie-pre-draft-asof-coverage-builder-v1-20260630"
VERDICT = "YELLOW_ROOKIE_PRE_DRAFT_ASOF_COVERAGE_BUILT_NO_EXPERIMENT_APPROVAL"
NOT_ENOUGH = "Not enough information"

SUBSTRATE_ROOT = (
    REPO_ROOT / "docs" / "hq" / "outcomes" / "nflverse_experiment_substrate_build_plan_v1_20260630"
)
PRE_DRAFT_COVERAGE_ROOT = (
    REPO_ROOT / "docs" / "hq" / "rookie_outcomes" / "rookie_pre_draft_feature_coverage_v1_20260630"
)
FEATURE_GATE_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_drafted_only_nflverse_feature_gate_evidence_v1_20260630"
)
PLAYER_CONTEXT_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nflverse_player_context_display_20260630"
)
DRAFTED_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_outcome_drafted_only_review_v1_20260630"
    / "drafted_only_outcome_player_audit.csv"
)
ENTRY_STATUS_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_entry_status_hygiene_v1_20260630"
    / "historical_rookie_entry_status_v1.csv"
)

ASOF_COLUMNS = (
    "feature_family",
    "source_artifact",
    "candidate_pre_draft_feature",
    "draft_event_feature",
    "post_draft_only",
    "row_count",
    "drafted_player_match_count",
    "missing_count",
    "as_of_field_present",
    "as_of_safe_now",
    "replay_safe_now",
    "experiment_ready_now",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "required_next_gate",
    "blocker_reason",
    "notes",
)

PLAYER_COLUMNS = (
    "player_name",
    "position",
    "draft_year",
    "nwr_player_id",
    "draft_pick_evidence_present",
    "draft_round_present",
    "overall_pick_present",
    "drafted_team_present",
    "combine_row_present",
    "prospect_age_present",
    "college_present",
    "identity_join_status",
    "review_required",
    "as_of_safe_now",
    "experiment_ready_now",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "blocker_reason",
    "notes",
)

ADMISSION_COLUMNS = (
    "player_id",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_team",
    "positive_draft_picks_evidence",
    "review_admission_status",
    "missingness_rule",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    source = load_source_data()
    matrix_rows = build_asof_rows(source)
    player_rows = build_player_rows(source)
    admission_rows = build_admission_rows(source)

    write_csv(args.output_root / "rookie_pre_draft_asof_coverage_matrix.csv", ASOF_COLUMNS, matrix_rows)
    write_csv(args.output_root / "drafted_only_player_feature_coverage.csv", PLAYER_COLUMNS, player_rows)
    write_csv(args.output_root / "rookie_drafted_admission_manifest.csv", ADMISSION_COLUMNS, admission_rows)
    write_docs(args.output_root, source, matrix_rows, player_rows, admission_rows)

    print(
        {
            "verdict": VERDICT,
            "base_head": BASE_HEAD,
            "asof_rows": len(matrix_rows),
            "player_rows": len(player_rows),
            "experiment_ready_count": sum(row["experiment_ready_now"] == "true" for row in matrix_rows),
        }
    )


def load_source_data() -> dict[str, object]:
    drafted_rows = read_csv(DRAFTED_AUDIT_PATH)
    entry_rows = read_csv(ENTRY_STATUS_PATH)
    feature_rows = read_csv(PRE_DRAFT_COVERAGE_ROOT / "rookie_pre_draft_feature_coverage_matrix.csv")
    feature_gate_rows = read_csv(FEATURE_GATE_ROOT / "rookie_feature_gate_matrix.csv")
    source_inputs = read_csv(SUBSTRATE_ROOT / "allowed_source_inputs.csv")
    player_context_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_display_artifact.csv")
    join_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_join_health.csv")
    build_report = (PLAYER_CONTEXT_ROOT / "nflverse_player_context_build_report.md").read_text(encoding="utf-8")
    asof_contract = (SUBSTRATE_ROOT / "rookie_pre_draft_asof_contract.md").read_text(encoding="utf-8")
    counts = build_counts(drafted_rows, entry_rows, feature_rows, player_context_rows, join_rows, build_report)
    entry_lookup = build_entry_lookup(entry_rows)
    return {
        "drafted_rows": drafted_rows,
        "entry_rows": entry_rows,
        "entry_lookup": entry_lookup,
        "feature_rows": feature_rows,
        "feature_gate_rows": feature_gate_rows,
        "source_inputs": source_inputs,
        "player_context_rows": player_context_rows,
        "join_rows": join_rows,
        "build_report": build_report,
        "asof_contract": asof_contract,
        "counts": counts,
    }


def build_counts(
    drafted_rows: list[dict[str, str]],
    entry_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
    player_context_rows: list[dict[str, str]],
    join_rows: list[dict[str, str]],
    build_report: str,
) -> dict[str, int | str]:
    draft_years = [int(row["draft_year"]) for row in drafted_rows if row["draft_year"].isdigit()]
    entry_status = Counter(row["entry_status"] for row in entry_rows)
    identity_status = Counter(row["identity_status"] for row in entry_rows)
    feature_by_name = {row["feature_family"]: row for row in feature_rows}
    join_by_gate = {row["gate"]: row for row in join_rows}
    draft_complete = sum(
        present(row["draft_year"])
        and present(row["draft_round"])
        and present(row["overall_pick"])
        and present(row["drafted_team"])
        for row in drafted_rows
    )
    return {
        "drafted_rows": len(drafted_rows),
        "draft_year_min": min(draft_years),
        "draft_year_max": max(draft_years),
        "draft_capital_complete": draft_complete,
        "drafted_entry_rows": entry_status["drafted"],
        "likely_udfa": entry_status["likely_udfa_needs_review"],
        "confirmed_udfa": entry_status["confirmed_udfa"],
        "identity_available": identity_status["draft_pick_identity_available"],
        "identity_partial": identity_status["draft_pick_identity_partial_missing_ids"],
        "player_context_rows": len(player_context_rows),
        "draft_picks_receipt_rows": extract_dataset_rows(build_report, "draft_picks"),
        "combine_receipt_rows": extract_dataset_rows(build_report, "combine"),
        "draft_capital_current_join_rows": join_by_gate["draft_capital_context_gate"]["clean_join_rows"],
        "combine_current_join_rows": join_by_gate["combine_context_gate"]["clean_join_rows"],
        "feature_experiment_ready_count": sum(row["experiment_safe_now"] == "true" for row in feature_rows),
        "prior_feature_rows": len(feature_rows),
        "prior_draft_picks_match_count": feature_by_name["draft_picks drafted admission"]["drafted_player_match_count"],
    }


def build_asof_rows(source: dict[str, object]) -> list[dict[str, str]]:
    counts = source["counts"]
    drafted = str(counts["drafted_rows"])
    receipt_combine = str(counts["combine_receipt_rows"])
    current_rows = str(counts["player_context_rows"])
    no_hist_match = "Not calculated at historical drafted player grain from tracked inputs"

    return [
        row("positive draft_picks evidence", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv", "false", "true", "false", drafted, drafted, "0", "false", "true_for_review_admission_only", "false", "Drafted-only as-of/replay HQ gate", "Positive draft-pick evidence supports drafted-only review only; no experiment approval.", "Admission evidence only."),
        row("draft year", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "false", "true", "false", drafted, drafted, "0", "false", "review_context_only_no_timestamp", "false", "Draft event as-of/replay HQ gate", "Draft year is review context, not experiment-ready.", "Factual draft event component."),
        row("draft round", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "false", "true", "false", drafted, drafted, "0", "false", "review_context_only_no_timestamp", "false", "Draft event as-of/replay HQ gate", "No fake round 8; not experiment-ready.", "Real draft rounds only."),
        row("overall pick", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "false", "true", "false", drafted, drafted, "0", "false", "review_context_only_no_timestamp", "false", "Draft event as-of/replay HQ gate", "Overall pick is review context, not experiment-ready.", "Factual draft event component."),
        row("drafted team", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "false", "true", "false", drafted, drafted, "0", "false", "review_context_only_no_timestamp", "false", "Team context/leakage HQ gate", "Drafted team can encode landing spot context; not experiment-ready.", "Review context only."),
        row("position", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "true", "false", "false", drafted, drafted, "0", "false", "review_context_only_no_timestamp", "false", "Position source/as-of HQ gate", "Position is candidate context but needs source/as-of contract before experiment.", "QB/RB/WR/TE drafted-only scope."),
        row("combine", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md", "true", "false", "false", receipt_combine, no_hist_match, NOT_ENOUGH, "false", "false", "false", "Combine historical coverage and event-date as-of gate", "Receipt exists but no tracked historical player-level combine match/as-of coverage in this packet.", "Candidate only."),
        row("prospect age", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "true", "false", "false", current_rows, no_hist_match, NOT_ENOUGH, "false", "false", "false", "Birthdate/age source and as-of gate", "Current derived roster age is display-only and not historical prospect age proof.", "Candidate only if later approved."),
        row("college/school", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv", "true", "false", "false", "0 approved tracked historical player rows", "0", drafted, "false", "false", "false", "College source-policy and identity gate", "No approved tracked player-grain college field is available in this packet.", "Do not infer from CFBD."),
        row("identity bridge health", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv", "false", "false", "false", drafted, str(counts["identity_available"]), str(counts["identity_partial"]), "false", "prerequisite_only", "false", "Identity approval/binding gate", "Identity bridge health is prerequisite evidence, not a feature.", "Partial missing ID rows require review."),
        row("rosters", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Point-in-time roster replay gate", "Roster/current status can leak and cannot prove UDFA.", "Blocked as pre-draft feature."),
        row("weekly_rosters", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Season-week point-in-time replay gate", "Weekly roster state can leak.", "Blocked as pre-draft feature."),
        row("injuries", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Availability/medical guardrail gate", "Missing injury is not healthy and injury context is not prospect risk.", "Blocked as pre-draft feature."),
        row("depth charts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Depth chart point-in-time replay gate", "Current role can leak and does not confirm UDFA.", "Display context only where separately approved."),
        row("snap_counts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Historical replay/leakage gate", "Future usage cannot be pre-draft feature.", "Missing snaps are not zero."),
        row("player_stats", "docs/hq/outcomes/nflverse_player_stats_sidecar_overlap_v1_20260630/", "false", "false", "true", current_rows, "sidecar only", NOT_ENOUGH, "false", "false", "false", "Label parity sidecar gate", "Future NFL production cannot be input feature.", "Sidecar/evaluation planning only."),
        row("schedules", "docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/", "false", "false", "true", "272", "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Schedule as-of/display gate", "Schedule context is not prospect feature or matchup signal.", "No Gate G approval."),
        row("contracts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Contract context policy gate", "Contract context is not rank/trade/value signal.", "Blocked as pre-draft feature."),
        row("current team/status", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "false", "true", current_rows, "not pre-draft feature", NOT_ENOUGH, "false", "false", "false", "Point-in-time current context gate", "Current team/status is post-draft context and can leak.", "Blocked as pre-draft feature."),
        row("CFBD joins", "docs/hq/rookie_model/; docs/hq/rookie_outcomes/", "false", "false", "false", "review packets only", "0 approved model/training joins", NOT_ENOUGH, "false", "false", "false", "CFBD identity/source approval gate", "CFBD model/training input remains blocked.", "Review-only context, not feature substrate."),
        row("UDFA status", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/", "false", "false", "false", str(counts["confirmed_udfa"]), "not drafted-only", str(counts["likely_udfa"]), "false", "false", "false", "Approved UDFA source-policy gate", "UDFA modeling remains blocked; draft absence is not confirmed UDFA.", "No UDFA experiment approval."),
        row("Outcome V2 labels", "docs/hq/outcomes/; docs/hq/rookie_outcomes/", "false", "false", "true", "review labels only", "label target only", NOT_ENOUGH, "false", "false", "false", "Label parity/model approval gate", "Labels are targets/evaluation only and never pre-draft features.", "No active probabilities."),
        row("ff_rankings", "docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/; policy gate", "false", "false", "false", "blocked", "0", NOT_ENOUGH, "false", "false", "false", "Blocked source-policy gate", "ff_rankings remains blocked.", "No ingestion/model/rank use."),
    ]


def row(
    feature_family: str,
    source_artifact: str,
    candidate_pre_draft_feature: str,
    draft_event_feature: str,
    post_draft_only: str,
    row_count: str,
    drafted_player_match_count: str,
    missing_count: str,
    as_of_field_present: str,
    as_of_safe_now: str,
    replay_safe_now: str,
    required_next_gate: str,
    blocker_reason: str,
    notes: str,
) -> dict[str, str]:
    return {
        "feature_family": feature_family,
        "source_artifact": source_artifact,
        "candidate_pre_draft_feature": candidate_pre_draft_feature,
        "draft_event_feature": draft_event_feature,
        "post_draft_only": post_draft_only,
        "row_count": row_count,
        "drafted_player_match_count": drafted_player_match_count,
        "missing_count": missing_count,
        "as_of_field_present": as_of_field_present,
        "as_of_safe_now": as_of_safe_now,
        "replay_safe_now": replay_safe_now,
        "experiment_ready_now": "false",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "required_next_gate": required_next_gate,
        "blocker_reason": blocker_reason,
        "notes": notes,
    }


def build_player_rows(source: dict[str, object]) -> list[dict[str, str]]:
    entry_lookup: dict[tuple[str, str, str, str], dict[str, str]] = source["entry_lookup"]
    rows: list[dict[str, str]] = []
    for drafted in source["drafted_rows"]:
        key = player_key(drafted)
        entry = entry_lookup.get(key, {})
        nwr_player_id = entry.get("nwr_player_id", NOT_ENOUGH)
        identity_status = entry.get("identity_status", NOT_ENOUGH)
        round_present = present(drafted["draft_round"])
        pick_present = present(drafted["overall_pick"])
        team_present = present(drafted["drafted_team"])
        blocker_bits = ["NO_EXPERIMENT_APPROVAL", "NO_AS_OF_TIMESTAMP_FIELD"]
        if not identity_status or identity_status == NOT_ENOUGH:
            blocker_bits.append("IDENTITY_STATUS_NOT_AVAILABLE")
        elif identity_status != "draft_pick_identity_available":
            blocker_bits.append(identity_status)
        rows.append(
            {
                "player_name": drafted["player_name"],
                "position": drafted["position"],
                "draft_year": drafted["draft_year"],
                "nwr_player_id": nwr_player_id,
                "draft_pick_evidence_present": "true",
                "draft_round_present": bool_text(round_present),
                "overall_pick_present": bool_text(pick_present),
                "drafted_team_present": bool_text(team_present),
                "combine_row_present": NOT_ENOUGH,
                "prospect_age_present": NOT_ENOUGH,
                "college_present": NOT_ENOUGH,
                "identity_join_status": identity_status,
                "review_required": "true",
                "as_of_safe_now": "false",
                "experiment_ready_now": "false",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "blocker_reason": ";".join(blocker_bits),
                "notes": "Drafted-only review evidence; combine/age/college as-of coverage not established.",
            }
        )
    return rows


def build_admission_rows(source: dict[str, object]) -> list[dict[str, str]]:
    entry_lookup: dict[tuple[str, str, str, str], dict[str, str]] = source["entry_lookup"]
    rows: list[dict[str, str]] = []
    for drafted in source["drafted_rows"]:
        entry = entry_lookup.get(player_key(drafted), {})
        player_id = (
            entry.get("nfl_player_id")
            or entry.get("gsis_id")
            or entry.get("player_stats_id")
            or entry.get("nwr_player_id")
            or NOT_ENOUGH
        )
        rows.append(
            {
                "player_id": player_id,
                "draft_year": drafted["draft_year"],
                "draft_round": drafted["draft_round"],
                "draft_pick": drafted["overall_pick"],
                "draft_team": drafted["drafted_team"],
                "positive_draft_picks_evidence": "true",
                "review_admission_status": "drafted_only_review_admission",
                "missingness_rule": "Missing draft capital is Not enough information and is not confirmed UDFA; fake round 8 is blocked.",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
            }
        )
    return rows


def write_docs(
    output_root: Path,
    source: dict[str, object],
    matrix_rows: list[dict[str, str]],
    player_rows: list[dict[str, str]],
    admission_rows: list[dict[str, str]],
) -> None:
    counts = source["counts"]
    docs = {
        "artifact_manifest.md": artifact_manifest(matrix_rows, player_rows, admission_rows),
        "rookie_pre_draft_asof_build_summary.md": build_summary(counts, matrix_rows, player_rows),
        "blocked_or_missing_pre_draft_sources.md": blocked_or_missing_sources(counts),
        "leakage_guardrail_report.md": leakage_guardrail_report(),
        "gate_e_f_g_status.md": gate_status(),
        "next_gate_recommendations.md": next_gate_recommendations(),
        "merge_safety_report.md": merge_safety_report(),
        "combine_asof_coverage_report.md": combine_asof_report(counts),
        "draft_capital_asof_report.md": draft_capital_asof_report(counts),
        "pre_draft_vs_post_draft_feature_report.md": pre_draft_vs_post_draft_report(),
        "gate_e_f_g_non_activation_report.md": gate_status(),
        "README.md": readme(),
    }
    for name, text in docs.items():
        (output_root / name).write_text(text.strip() + "\n", encoding="utf-8")


def artifact_manifest(
    matrix_rows: list[dict[str, str]],
    player_rows: list[dict[str, str]],
    admission_rows: list[dict[str, str]],
) -> str:
    return f"""
# Artifact Manifest

Verdict: `{VERDICT}`

Branch: `{BRANCH}`

Worktree: `{WORKTREE}`

Base HEAD: `{BASE_HEAD}`

This packet builds tracked, review-only drafted-only rookie pre-draft as-of coverage evidence from tracked inputs only. It does not read raw shared data and grants no experiment, model, training, source-truth, Gate G, app, UDFA, or CFBD model/training approval.

| Artifact | Rows | Purpose |
|---|---:|---|
| `rookie_pre_draft_asof_coverage_matrix.csv` | {len(matrix_rows)} | Feature-family as-of coverage and blocker matrix |
| `drafted_only_player_feature_coverage.csv` | {len(player_rows)} | Player-level drafted-only coverage substrate |
| `rookie_drafted_admission_manifest.csv` | {len(admission_rows)} | Contract companion drafted admission manifest |
| `rookie_pre_draft_asof_build_summary.md` | n/a | Summary and verdict |
| `blocked_or_missing_pre_draft_sources.md` | n/a | Missing as-of/source evidence |
| `leakage_guardrail_report.md` | n/a | Leakage and as-of guardrails |
| `gate_e_f_g_status.md` | n/a | Non-activation gate status |
| `next_gate_recommendations.md` | n/a | Recommended next evidence lanes |
| `merge_safety_report.md` | n/a | Protected-path and approval boundary |
| `combine_asof_coverage_report.md` | n/a | Contract companion combine report |
| `draft_capital_asof_report.md` | n/a | Contract companion draft capital report |
| `pre_draft_vs_post_draft_feature_report.md` | n/a | Contract companion feature timing report |
| `gate_e_f_g_non_activation_report.md` | n/a | Contract companion non-activation report |
"""


def build_summary(counts: dict[str, int | str], matrix_rows: list[dict[str, str]], player_rows: list[dict[str, str]]) -> str:
    experiment_ready = sum(row["experiment_ready_now"] == "true" for row in matrix_rows)
    player_experiment_ready = sum(row["experiment_ready_now"] == "true" for row in player_rows)
    return f"""
# Rookie Pre-Draft As-Of Build Summary

Verdict: `{VERDICT}`

Inputs were limited to tracked review/policy artifacts. No raw `C:\\NWR_SHARED_DATA`, local cache, vendor, Gmail, or private files were read.

Coverage:

- Drafted-only QB/RB/WR/TE player rows: `{counts["drafted_rows"]}`
- Rookie classes: `{counts["draft_year_min"]}` through `{counts["draft_year_max"]}`
- Draft-capital complete rows: `{counts["draft_capital_complete"]}`
- Positive drafted entry rows from hygiene artifact: `{counts["drafted_entry_rows"]}`
- Current NFLVerse draft_picks receipt rows: `{counts["draft_picks_receipt_rows"]}`
- Current NFLVerse combine receipt rows: `{counts["combine_receipt_rows"]}`
- Historical player-level combine as-of matches: `Not enough information`
- Feature-family experiment-ready rows: `{experiment_ready}`
- Player-level experiment-ready rows: `{player_experiment_ready}`

Drafted-only review may proceed from positive draft-pick evidence. Draft event fields remain review context only. Combine, prospect age, college/school, and identity bridge health need further source/as-of/replay gates before any experiment planning.
"""


def blocked_or_missing_sources(counts: dict[str, int | str]) -> str:
    return f"""
# Blocked Or Missing Pre-Draft Sources

Missing or blocked source evidence:

- Historical player-level combine rows matched to the `{counts["drafted_rows"]}` drafted-only audit rows are not available as tracked as-of substrate in this packet.
- Prospect age is available only as current display-derived roster age in the player-context artifact; that is not historical prospect-age proof.
- College/school is not present as an approved tracked player-grain field for this packet.
- CFBD remains review-only and blocked from model/training input.
- UDFA status remains blocked; draft absence is not confirmed UDFA.
- Fake round `8`, missing-as-zero, and synthetic draft capital remain blocked.
- Future NFL production/current context cannot be pre-draft features.
"""


def leakage_guardrail_report() -> str:
    return """
# Leakage Guardrail Report

All rows keep `experiment_ready_now=false`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`.

Required before future experiment design:

- prediction anchor;
- source extraction timestamp;
- feature as-of timestamp;
- point-in-time replay manifest;
- identity-safe join manifest;
- missingness policy;
- leakage audit;
- class-year split plan;
- label/feature separation proof;
- blocked-source scan.

Post-draft/current fields remain blocked as pre-draft features: rosters, weekly_rosters, injuries, depth charts, snap_counts, player_stats, schedules, contracts, current team/status, and Outcome V2 labels. Missing values remain `Not enough information`, never zero, false, clean, healthy, low-risk, or confirmed UDFA.
"""


def gate_status() -> str:
    return """
# Gate E/F/G Status

Gate E remains review/R&D only. This packet creates substrate evidence, not an experiment.

Gate F remains non-activated or partial display/review only where separately approved. This packet does not create display outputs.

Gate G remains blocked. No Rankings, Draft Room, Player Compare, app wiring, hidden sort, active rookie probabilities, fake T12/T24/T36 outputs, or release approval is granted.
"""


def next_gate_recommendations() -> str:
    return """
# Next Gate Recommendations

Safe next evidence lanes:

- historical combine player-match and event-date as-of audit;
- prospect age source/as-of audit;
- college/school source-policy and identity audit;
- point-in-time snapshot manifest build for candidate draft-event features;
- identity partial-missing-ID review for drafted historical rows.

Still blocked:

- model training;
- experiment execution;
- active rookie probabilities;
- UDFA modeling;
- CFBD model/training input;
- Gate G and Rankings wiring.
"""


def merge_safety_report() -> str:
    return """
# Merge Safety Report

This lane creates docs, CSV audit matrices, a non-runtime report builder, and focused tests only.

Confirmed:

- no app files changed;
- no Rankings, Gate F/G, Draft Room, Player Compare, or app behavior changed;
- no model outputs changed;
- no source-truth behavior changed;
- no pinned snapshots changed;
- no `latest_candidate` or `latest_approved` changed;
- no protected/raw/private paths tracked;
- no secrets tracked;
- no local_exports, raw, cache, vendor, Gmail, or shared-data files tracked.
"""


def combine_asof_report(counts: dict[str, int | str]) -> str:
    return f"""
# Combine As-Of Coverage Report

Tracked NFLVerse player-context build report lists combine receipt rows: `{counts["combine_receipt_rows"]}`.

Current player-context combine clean joins: `{counts["combine_current_join_rows"]}` out of `{counts["player_context_rows"]}` current rows.

This does not prove historical drafted-only player-level combine coverage, event-date availability, extraction timestamp, or replay safety for the `{counts["drafted_rows"]}` drafted audit rows.

Result: combine is a candidate only. `experiment_ready_now=false`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`.
"""


def draft_capital_asof_report(counts: dict[str, int | str]) -> str:
    return f"""
# Draft Capital As-Of Report

Historical drafted audit rows: `{counts["drafted_rows"]}`.

Rows with complete draft event context in the tracked drafted audit: `{counts["draft_capital_complete"]}`.

Tracked NFLVerse player-context build report lists draft_picks receipt rows: `{counts["draft_picks_receipt_rows"]}`.

Positive draft-pick evidence supports drafted-only review admission. It does not approve experiments, model use, training use, source truth, Gate G, or active rookie probabilities.

Missing draft capital is `Not enough information`, not confirmed UDFA. Fake round `8` remains blocked.
"""


def pre_draft_vs_post_draft_report() -> str:
    return """
# Pre-Draft Vs Post-Draft Feature Report

Draft event review context:

- positive draft_picks evidence;
- draft year;
- draft round;
- overall pick;
- drafted team;
- position, pending source/as-of gate.

Candidate pre-draft context requiring further evidence:

- combine;
- prospect age;
- college/school;
- identity bridge health as prerequisite evidence only.

Blocked as pre-draft features:

- rosters;
- weekly_rosters;
- injuries;
- depth charts;
- snap_counts;
- player_stats;
- schedules;
- contracts;
- current team/status;
- Outcome V2 labels;
- CFBD joins;
- UDFA status;
- ff_rankings.
"""


def readme() -> str:
    return f"""
# Rookie Pre-Draft As-Of Coverage Builder V1

Verdict: `{VERDICT}`

This packet builds review-only drafted-only rookie pre-draft as-of coverage evidence. It does not approve experiments, model/training/source-truth use, rookie probabilities, Gate G, UDFA modeling, CFBD model/training input, or app wiring.
"""


def build_entry_lookup(entry_rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {player_key(row): row for row in entry_rows if row.get("entry_status") == "drafted"}


def player_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("player_name", ""),
        row.get("position", ""),
        row.get("draft_year", "") or row.get("rookie_class_year", ""),
        row.get("overall_pick", "") or row.get("draft_pick", ""),
    )


def present(value: str) -> bool:
    return value not in {"", NOT_ENOUGH, "None", "null"}


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def extract_dataset_rows(report: str, dataset: str) -> int:
    pattern = rf"\| {re.escape(dataset)} \| [^|]+ \| (\d+) \|"
    match = re.search(pattern, report)
    return int(match.group(1)) if match else 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
