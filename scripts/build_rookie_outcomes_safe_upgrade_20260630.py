from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_outcomes_safe_upgrade_20260630"
)

ENTRY_STATUS_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_entry_status_hygiene_v1_20260630"
    / "historical_rookie_entry_status_v1.csv"
)
DRAFTED_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_outcome_drafted_only_review_v1_20260630"
    / "drafted_only_outcome_player_audit.csv"
)
DRAFTED_COVERAGE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_outcome_drafted_only_review_v1_20260630"
    / "drafted_only_outcome_coverage.csv"
)
V5_DISPLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "udfa_review_application_v1_20260630"
    / "rookie_display_artifact_v5_coverage_matrix.csv"
)
SOURCE_RECON_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_source_availability_reconciliation_20260630"
    / "source_availability_matrix.csv"
)

BASE_HEAD = "85eb3d0607a4370d9aba50aae39fd0d35934c4be"
RUN_ID = "rookie_outcomes_safe_upgrade_20260630"
NOT_ENOUGH = "Not enough information"

GATE_COLUMNS = (
    "gate_or_area",
    "current_status",
    "input_artifact",
    "approved_action",
    "blocked_action",
    "row_count",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
    "notes",
)

SOURCE_COLUMNS = (
    "source_name",
    "source_type",
    "source_policy_status",
    "coverage_count",
    "allowed_review_use",
    "blocked_use",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "notes",
)

FEATURE_COLUMNS = (
    "feature_name",
    "source",
    "population_scope",
    "allowed_for_review_reporting",
    "allowed_for_future_review_only_rd",
    "active_probability_column_allowed",
    "rankings_wiring_allowed",
    "model_use_allowed",
    "training_allowed",
    "missing_value_policy",
    "blocker_reason",
    "notes",
    "review_only",
)

DISPLAY_COLUMNS = (
    "artifact_name",
    "row_count",
    "drafted_review_rate_rows",
    "confirmed_udfa_status_only_rows",
    "not_enough_information_rows",
    "wrong_universe_blocked_rows",
    "rankings_wiring_allowed_rows",
    "model_use_allowed_rows",
    "training_allowed_rows",
    "active_probability_columns_created",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "notes",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    entry_rows = read_csv(ENTRY_STATUS_PATH)
    drafted_rows = read_csv(DRAFTED_AUDIT_PATH)
    coverage_rows = read_csv(DRAFTED_COVERAGE_PATH)
    display_rows = read_csv(V5_DISPLAY_PATH)
    source_recon_rows = read_csv(SOURCE_RECON_PATH)

    counts = build_counts(entry_rows, drafted_rows, coverage_rows, display_rows)
    gate_rows = build_gate_rows(counts)
    source_rows = build_source_rows(counts, source_recon_rows)
    feature_rows = build_feature_rows()
    display_audit_rows = build_display_rows(counts)

    write_csv(args.output_root / "rookie_safe_upgrade_gate_matrix.csv", GATE_COLUMNS, gate_rows)
    write_csv(
        args.output_root / "rookie_safe_upgrade_source_policy_matrix.csv",
        SOURCE_COLUMNS,
        source_rows,
    )
    write_csv(
        args.output_root / "rookie_safe_upgrade_feature_policy_matrix.csv",
        FEATURE_COLUMNS,
        feature_rows,
    )
    write_csv(
        args.output_root / "rookie_safe_upgrade_display_artifact_audit.csv",
        DISPLAY_COLUMNS,
        display_audit_rows,
    )
    write_docs(args.output_root, counts)

    print(
        {
            "verdict": "YELLOW_SAFE_UPGRADE_REVIEW_ONLY",
            "drafted_rows": counts["drafted_rows"],
            "drafted_any_label_rows": counts["drafted_any_label_rows"],
            "v5_rows": counts["v5_rows"],
            "confirmed_udfa_review_only_status_rows": counts["v5_confirmed_udfa"],
            "active_probability_columns": 0,
            "gate_g": "BLOCKED",
        }
    )


def build_counts(
    entry_rows: list[dict[str, str]],
    drafted_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
) -> dict[str, int]:
    entry_counts = Counter(row["entry_status"] for row in entry_rows)
    display_status = Counter(row["display_status"] for row in display_rows)
    udfa_status = Counter(row["udfa_status"] for row in display_rows)
    return {
        "entry_total": len(entry_rows),
        "entry_drafted": entry_counts["drafted"],
        "entry_likely_udfa": entry_counts["likely_udfa_needs_review"],
        "entry_confirmed_udfa": entry_counts["confirmed_udfa"],
        "entry_wrong_universe": entry_counts["wrong_universe"],
        "entry_name_collision": entry_counts["name_collision"],
        "drafted_rows": len(drafted_rows),
        "coverage_groups": len(coverage_rows),
        "drafted_any_label_rows": sum(
            row["outcome_window_status"] != "missing_outcome_label"
            for row in drafted_rows
        ),
        "drafted_rookie_year_labels": sum(
            row["has_rookie_year_label"] == "true" for row in drafted_rows
        ),
        "drafted_2y_labels": sum(row["has_2y_label"] == "true" for row in drafted_rows),
        "drafted_3y_labels": sum(row["has_3y_label"] == "true" for row in drafted_rows),
        "drafted_5y_labels": sum(row["has_5y_label"] == "true" for row in drafted_rows),
        "v5_rows": len(display_rows),
        "v5_outcome_rate": display_status["review_only_display_fields_available"],
        "v5_confirmed_udfa": udfa_status["confirmed_udfa_review_only"],
        "v5_not_enough": display_status[NOT_ENOUGH],
        "v5_wrong_universe": display_status["wrong_universe_blocked"],
        "v5_rankings_allowed": sum(
            row["rankings_wiring_allowed"] == "true" for row in display_rows
        ),
        "v5_model_allowed": sum(row["model_use_allowed"] == "true" for row in display_rows),
        "v5_training_allowed": sum(
            row["training_allowed"] == "true" for row in display_rows
        ),
    }


def build_gate_rows(counts: dict[str, int]) -> list[dict[str, str]]:
    return [
        gate_row(
            "entry_status_hygiene",
            "YELLOW_REVIEW_ONLY",
            "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/"
            "historical_rookie_entry_status_v1.csv",
            "Use `entry_status=drafted` for drafted-only review coverage.",
            "UDFA modeling, training, source truth, and fake UDFA inference.",
            counts["entry_total"],
            "Draft absence cannot confirm UDFA.",
        ),
        gate_row(
            "drafted_only_outcome_review",
            "YELLOW_DRAFTED_ONLY_REVIEW_READY",
            "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/",
            "Drafted QB/RB/WR/TE review-only label coverage reporting.",
            "Model tuning, scoring, active probability columns, app wiring.",
            counts["drafted_rows"],
            "Label coverage is review-only and incomplete outside available windows.",
        ),
        gate_row(
            "current_rookie_v5_display_audit",
            "REVIEW_ONLY_STATUS_AUDIT",
            "docs/hq/rookie_outcomes/udfa_review_application_v1_20260630/"
            "rookie_display_artifact_v5_coverage_matrix.csv",
            "Audit existing review-only V5 status/display coverage.",
            "New active display artifact, Rankings wiring, hidden sort logic.",
            counts["v5_rows"],
            "V5 remains display/status review-only; no release approval.",
        ),
        gate_row(
            "udfa_modeling",
            "BLOCKED_NO_APPROVED_UDFA_SOURCE",
            "docs/hq/rookie_model/rookie_source_availability_reconciliation_20260630/",
            "Keep blockers explicit.",
            "Combined drafted + UDFA modeling and clean UDFA promotion.",
            counts["entry_likely_udfa"],
            "No tracked approved source unblocks UDFA/non-drafted modeling.",
        ),
        gate_row(
            "gate_f",
            "BLOCKED_FOR_MODEL_READY",
            "review-only artifacts",
            "Review-only drafted-player coverage reporting may be planned.",
            "Model-ready Gate F release from this lane.",
            0,
            "No new Gate F artifact created in this safe-upgrade lane.",
        ),
        gate_row(
            "gate_g",
            "BLOCKED_NEEDS_RANKINGS_WIRING_APPROVAL",
            "review-only artifacts",
            "Keep release audit closed.",
            "Rankings integration and current-player rookie outcome columns.",
            0,
            "No app/rankings wiring is approved.",
        ),
    ]


def build_source_rows(
    counts: dict[str, int],
    source_recon_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    no_approved_sources = sum(
        row["approved_for_model_use"] == "yes" or row["approved_for_training"] == "yes"
        for row in source_recon_rows
    )
    return [
        source_row(
            "nflverse draft_picks",
            "public factual structured draft data",
            "allowed_review_only_for_drafted_rows",
            counts["entry_drafted"],
            "Drafted-player identity/draft-capital review and coverage.",
            "UDFA confirmation from absence; fake round 8; model/training source truth.",
            "Draft absence remains evidence only, not UDFA proof.",
        ),
        source_row(
            "nflverse combine / measurements",
            "public factual structured measurements",
            "display_context_only_pending_validation",
            72,
            "Review-only factual measurement context when already joined safely.",
            "Training/model promotion in this lane.",
            "Combine context remains outside active rookie outcome modeling.",
        ),
        source_row(
            "nflverse rosters / depth charts",
            "public factual structured roster/depth context",
            "blocked_no_populated_approved_depth_chart_source",
            0,
            "No use in this lane.",
            "Depth-chart non-drafted watchlist or model features.",
            "HQ reconciliation found schema-only/no approved populated rows.",
        ),
        source_row(
            "CFBD review artifacts",
            "college context / identity candidates",
            "candidate_only_review_only",
            0,
            "Candidate-only context with human review requirements.",
            "CFBD model input, training truth, automatic identity joins.",
            "Historical CFBD identities remain unapproved for model input.",
        ),
        source_row(
            "Outcome V2 historical labels",
            "factual NFL target labels",
            "target_labels_review_only",
            counts["drafted_any_label_rows"],
            "Drafted-only label coverage analysis as targets only.",
            "Input features, future production leakage, app scoring.",
            "Labels are never promoted to input features here.",
        ),
        source_row(
            "Gmail / vendor / RotoWire / FantasyPros / FootballDB",
            "blocked private/vendor/scraped sources",
            "blocked",
            0,
            "No use.",
            "Scraping, ingestion, model input, display source truth.",
            "Forbidden by lane guardrails.",
        ),
        source_row(
            "source availability reconciliation",
            "tracked HQ audit",
            "YELLOW_NO_APPROVED_SOURCES_FOUND",
            no_approved_sources,
            "Use as blocker evidence.",
            "Treat as approval for new source/model gates.",
            "No approved tracked source unblocks remaining non-drafted blockers.",
        ),
    ]


def build_feature_rows() -> list[dict[str, str]]:
    rows = [
        feature_row(
            "position",
            "nflverse draft_picks / entry status",
            "drafted_only",
            "true",
            "true",
            "Factual class/position context only.",
        ),
        feature_row(
            "draft_year",
            "nflverse draft_picks",
            "drafted_only",
            "true",
            "true",
            "Factual class context.",
        ),
        feature_row(
            "rookie_class_year",
            "entry status hygiene",
            "drafted_only",
            "true",
            "true",
            "Factual class context when sourced from draft/entry artifact.",
        ),
        feature_row(
            "draft_round",
            "nflverse draft_picks",
            "drafted_only",
            "true",
            "true",
            "Post-draft factual feature for future review-only R&D only.",
        ),
        feature_row(
            "overall_pick",
            "nflverse draft_picks",
            "drafted_only",
            "true",
            "true",
            "Post-draft factual feature for future review-only R&D only.",
        ),
        feature_row(
            "draft_capital_bucket",
            "derived from draft round/pick",
            "drafted_only",
            "true",
            "true",
            "No fake round 8; unknown remains Not enough information.",
        ),
        feature_row(
            "confirmed_udfa_review_only_status",
            "user accepted review-only UDFA status packet",
            "current_rookie_status_only",
            "true",
            "false",
            "Status-only display context; not model/training/source truth.",
        ),
        feature_row(
            "likely_udfa_needs_review",
            "draft absence / candidate evidence",
            "blocked",
            "false",
            "false",
            "Draft absence cannot confirm UDFA.",
        ),
        feature_row(
            "CFBD production",
            "CFBD review artifacts",
            "blocked",
            "false",
            "false",
            "Candidate-only rows remain review-only and identity-review-required.",
        ),
        feature_row(
            "future NFL production / Outcome labels",
            "Outcome V2 labels",
            "target_only",
            "false",
            "false",
            "Blocked as input feature due to leakage.",
        ),
    ]
    return rows


def build_display_rows(counts: dict[str, int]) -> list[dict[str, str]]:
    return [
        {
            "artifact_name": "rookie_display_artifact_v5_coverage_matrix.csv",
            "row_count": str(counts["v5_rows"]),
            "drafted_review_rate_rows": str(counts["v5_outcome_rate"]),
            "confirmed_udfa_status_only_rows": str(counts["v5_confirmed_udfa"]),
            "not_enough_information_rows": str(counts["v5_not_enough"]),
            "wrong_universe_blocked_rows": str(counts["v5_wrong_universe"]),
            "rankings_wiring_allowed_rows": str(counts["v5_rankings_allowed"]),
            "model_use_allowed_rows": str(counts["v5_model_allowed"]),
            "training_allowed_rows": str(counts["v5_training_allowed"]),
            "active_probability_columns_created": "0",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "notes": (
                "Existing V5 is audited only. No new display artifact, app wiring, "
                "hidden sort, or active rookie probability columns are created."
            ),
        }
    ]


def gate_row(
    gate_or_area: str,
    current_status: str,
    input_artifact: str,
    approved_action: str,
    blocked_action: str,
    row_count: int,
    notes: str,
) -> dict[str, str]:
    return {
        "gate_or_area": gate_or_area,
        "current_status": current_status,
        "input_artifact": input_artifact,
        "approved_action": approved_action,
        "blocked_action": blocked_action,
        "row_count": str(row_count),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
        "notes": notes,
    }


def source_row(
    source_name: str,
    source_type: str,
    source_policy_status: str,
    coverage_count: int,
    allowed_review_use: str,
    blocked_use: str,
    notes: str,
) -> dict[str, str]:
    return {
        "source_name": source_name,
        "source_type": source_type,
        "source_policy_status": source_policy_status,
        "coverage_count": str(coverage_count),
        "allowed_review_use": allowed_review_use,
        "blocked_use": blocked_use,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "notes": notes,
    }


def feature_row(
    feature_name: str,
    source: str,
    population_scope: str,
    allowed_for_review_reporting: str,
    allowed_for_future_review_only_rd: str,
    notes: str,
) -> dict[str, str]:
    blocked_reason = NOT_ENOUGH
    if allowed_for_review_reporting == "false":
        blocked_reason = "blocked_by_source_policy_or_leakage"
    return {
        "feature_name": feature_name,
        "source": source,
        "population_scope": population_scope,
        "allowed_for_review_reporting": allowed_for_review_reporting,
        "allowed_for_future_review_only_rd": allowed_for_future_review_only_rd,
        "active_probability_column_allowed": "false",
        "rankings_wiring_allowed": "false",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "missing_value_policy": NOT_ENOUGH,
        "blocker_reason": blocked_reason,
        "notes": notes,
        "review_only": "true",
    }


def write_docs(root: Path, counts: dict[str, int]) -> None:
    write_doc(
        root / "artifact_manifest.md",
        [
            "# Rookie Outcomes Safe Upgrade - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`YELLOW_SAFE_UPGRADE_REVIEW_ONLY`",
            "",
            "This packet implements only HQ-approved safe steps: consolidate source policy,",
            "feature policy, gate status, and existing review-only display coverage. It does",
            "not train, tune, score, app-wire, or release rookie outcome columns.",
            "",
            "## Inputs",
            "",
            "- Rookie Entry Status Hygiene V1",
            "- Drafted-Only Rookie Outcome Review V1",
            "- UDFA Review Application V1 / Gate F V5 coverage matrix",
            "- Rookie Source Availability Reconciliation",
            "- Prior Gate D/E/F policy docs and matrices",
            "",
            "## Outputs",
            "",
            "- `rookie_safe_upgrade_gate_matrix.csv`",
            "- `rookie_safe_upgrade_source_policy_matrix.csv`",
            "- `rookie_safe_upgrade_feature_policy_matrix.csv`",
            "- `rookie_safe_upgrade_display_artifact_audit.csv`",
            "- `safe_upgrade_summary.md`",
            "- `remaining_blockers.md`",
            "- `merge_safety_report.md`",
            "- `README.md`",
            "",
            "All outputs are review-only and keep `model_use_allowed=false` and",
            "`training_allowed=false`.",
        ],
    )
    write_doc(
        root / "safe_upgrade_summary.md",
        [
            "# Safe Upgrade Summary",
            "",
            f"- Base HEAD: `{BASE_HEAD}`",
            "- Verdict: `YELLOW_SAFE_UPGRADE_REVIEW_ONLY`",
            f"- Entry-status rows reviewed: {counts['entry_total']}",
            f"- Drafted entry-status rows: {counts['entry_drafted']}",
            f"- Drafted-only outcome rows: {counts['drafted_rows']}",
            f"- Drafted rows with any Outcome V2 label linkage: {counts['drafted_any_label_rows']}",
            f"- Current V5 display/status rows audited: {counts['v5_rows']}",
            f"- Existing drafted review-rate rows: {counts['v5_outcome_rate']}",
            f"- Confirmed UDFA review-only status rows: {counts['v5_confirmed_udfa']}",
            "",
            "No active rookie probability columns, Rankings wiring, model input promotion,",
            "CFBD training truth, UDFA modeling approval, or fake outputs were created.",
        ],
    )
    write_doc(
        root / "remaining_blockers.md",
        [
            "# Remaining Blockers",
            "",
            f"- Likely UDFA needs review rows remain blocked: {counts['entry_likely_udfa']}",
            f"- Confirmed UDFA rows approved for modeling: {counts['entry_confirmed_udfa']}",
            f"- Wrong-universe rows remain blocked: {counts['entry_wrong_universe']}",
            f"- Name-collision rows remain blocked: {counts['entry_name_collision']}",
            "- Draft absence cannot confirm UDFA.",
            "- Missing draft capital remains `Not enough information`, never zero.",
            "- Fake round 8 is not allowed.",
            "- CFBD candidate-only rows remain review-only and cannot become training truth.",
            "- Gate F model-ready release remains blocked.",
            "- Gate G / Rankings wiring remains blocked.",
        ],
    )
    write_doc(
        root / "merge_safety_report.md",
        [
            "# Merge Safety Report",
            "",
            "- Docs/CSV/tests only.",
            "- No app files changed.",
            "- No Rankings, Live Draft, Mock Draft, Gate F, or Gate G behavior changed.",
            "- No model outputs changed.",
            "- No `final_board_rank`, Dynasty Rank, Candidate Rank, tiers, pinned snapshots,",
            "  `latest_candidate`, or `latest_approved` changed.",
            "- No source-truth/model-input gate changed.",
            "- No shared/private/raw/cache/runtime/secrets files are tracked.",
        ],
    )
    write_doc(
        root / "README.md",
        [
            "# Rookie Outcomes Safe Upgrade",
            "",
            "This folder is a conservative HQ safe-upgrade packet. It closes the loop on",
            "what can proceed after the drafted-only review and UDFA hygiene work: review-only",
            "reporting may continue, but model/training/app release gates remain closed.",
        ],
    )


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


if __name__ == "__main__":
    main()
