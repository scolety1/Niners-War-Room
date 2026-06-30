# ruff: noqa: E501

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
    / "rookie_outcomes_drafted_only_feature_policy_safe_upgrade_20260630"
)

ENTRY_STATUS_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_entry_status_hygiene_v1_20260630"
    / "historical_rookie_entry_status_v1.csv"
)
SOURCE_AVAILABILITY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_source_availability_reconciliation_20260630"
    / "source_availability_matrix.csv"
)
DRAFTED_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_outcome_drafted_only_review_v1_20260630"
    / "drafted_only_outcome_player_audit.csv"
)
DISPLAY_V5_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "udfa_review_application_v1_20260630"
    / "rookie_display_artifact_v5_coverage_matrix.csv"
)

BASE_HEAD = "e598249a2a9915366fc2087991bb0519be7c8403"
BRANCH = "work/lane-rookie-outcomes-upgrade-20260630"
WORKTREE = r"C:\NWR\Niners-War-Room-lane-rookie-outcomes-upgrade-20260630"
VERDICT = "YELLOW_DRAFTED_ONLY_FEATURE_POLICY_SAFE_UPGRADE"
WAIT = "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN"
NOT_ENOUGH = "Not enough information"

STATUS_COLUMNS = (
    "finding_id",
    "area",
    "recommendation",
    "classification",
    "current_repo_status",
    "implemented_in_this_lane",
    "output_path_or_test",
    "guardrail_risk",
    "blocker_reason",
    "next_gate",
    "notes",
)

ADMISSION_COLUMNS = (
    "rule_id",
    "rule_name",
    "source",
    "required_condition",
    "allowed_result",
    "blocked_result",
    "missing_data_behavior",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "test_required",
)

FEATURE_COLUMNS = (
    "feature_name",
    "current_source_or_service",
    "appears_in_replay_contract",
    "approved_in_gate_e_six_feature_cap",
    "pre_draft_allowed",
    "post_draft_allowed",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "blocked_leakage",
    "downgrade_behavior",
    "required_gate",
    "notes",
)

LABEL_COLUMNS = (
    "label_family",
    "source_path_or_dataset",
    "current_status",
    "allowed_as_label_target",
    "allowed_as_feature",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "refresh_dependency",
    "blocker_reason",
    "next_gate",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    entry_rows = read_csv(ENTRY_STATUS_PATH)
    source_rows = read_csv(SOURCE_AVAILABILITY_PATH)
    drafted_rows = read_csv(DRAFTED_AUDIT_PATH)
    display_rows = read_csv(DISPLAY_V5_PATH)
    counts = build_counts(entry_rows, source_rows, drafted_rows, display_rows)

    write_csv(
        args.output_root / "rookie_outcomes_safe_upgrade_status_matrix.csv",
        STATUS_COLUMNS,
        build_status_rows(),
    )
    write_csv(
        args.output_root / "drafted_only_admission_gate_contract.csv",
        ADMISSION_COLUMNS,
        build_admission_rows(),
    )
    write_csv(
        args.output_root / "gate_e_feature_policy_manifest.csv",
        FEATURE_COLUMNS,
        build_feature_rows(),
    )
    write_csv(
        args.output_root / "label_source_partition_matrix.csv",
        LABEL_COLUMNS,
        build_label_rows(),
    )
    write_docs(args.output_root, counts)
    print(
        {
            "verdict": VERDICT,
            "base_head": BASE_HEAD,
            "output_root": str(args.output_root),
            "drafted_rows": counts["drafted_rows"],
            "display_rows": counts["display_rows"],
            "refresh_health_dependency": WAIT,
        }
    )


def build_counts(
    entry_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    drafted_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
) -> dict[str, int | str]:
    entry_status = Counter(row["entry_status"] for row in entry_rows)
    display_status = Counter(row["display_status"] for row in display_rows)
    udfa_status = Counter(row["udfa_status"] for row in display_rows)

    depth_rows = [row for row in source_rows if row["blocker_area"] == "depth_chart"]
    populated_depth_rows = [
        row for row in depth_rows if row["available_now"] == "yes" and row["row_count"] != "0"
    ]
    depth_template = next(
        (row for row in depth_rows if row["source_name"] == "nflverse depth chart weekly template"),
        {},
    )
    rotowire_depth = next(
        (
            row
            for row in depth_rows
            if row["source_name"] == "RotoWire May 22 depth chart snapshot documentation"
        ),
        {},
    )

    return {
        "entry_total": len(entry_rows),
        "entry_drafted": entry_status["drafted"],
        "entry_likely_udfa": entry_status["likely_udfa_needs_review"],
        "entry_wrong_universe": entry_status["wrong_universe"],
        "entry_name_collision": entry_status["name_collision"],
        "entry_confirmed_udfa": entry_status["confirmed_udfa"],
        "drafted_rows": len(drafted_rows),
        "drafted_any_label": sum(
            row["outcome_window_status"] != "missing_outcome_label" for row in drafted_rows
        ),
        "drafted_rookie_year": sum(
            row["has_rookie_year_label"] == "true" for row in drafted_rows
        ),
        "drafted_2y": sum(row["has_2y_label"] == "true" for row in drafted_rows),
        "drafted_3y": sum(row["has_3y_label"] == "true" for row in drafted_rows),
        "drafted_5y": sum(row["has_5y_label"] == "true" for row in drafted_rows),
        "display_rows": len(display_rows),
        "display_review_fields": display_status["review_only_display_fields_available"],
        "display_udfa_status_only": udfa_status["confirmed_udfa_review_only"],
        "display_not_enough": display_status[NOT_ENOUGH],
        "display_wrong_universe": display_status["wrong_universe_blocked"],
        "display_model_true": sum(row["model_use_allowed"] == "true" for row in display_rows),
        "display_training_true": sum(row["training_allowed"] == "true" for row in display_rows),
        "display_rankings_true": sum(
            row["rankings_wiring_allowed"] == "true" for row in display_rows
        ),
        "depth_chart_populated_sources": len(populated_depth_rows),
        "depth_chart_template_row_count": depth_template.get("row_count", "0"),
        "rotowire_depth_documented_count": rotowire_depth.get("row_count", "0"),
    }


def build_status_rows() -> list[dict[str, str]]:
    return [
        status_row(
            "RO-001",
            "drafted_only_universe",
            "Use positive nflverse draft_picks evidence as the drafted-only admission gate.",
            "SAFE_NOW",
            "Drafted-only historical review artifacts exist, but this lane makes the gate explicit.",
            "yes",
            "drafted_only_admission_gate_contract.md",
            "Medium",
            "Other datasets may enrich identity only; they cannot admit drafted status.",
            "Gate D policy receipt",
            "Implemented as policy/spec only; no dataset pull.",
        ),
        status_row(
            "RO-002",
            "draft_capital_bucketing",
            "Quarantine synthetic round-8 and pseudo draft capital outside model buckets.",
            "SAFE_NOW",
            "Prior Gate F reported round-8-like display states without allowed buckets.",
            "yes",
            "synthetic_draft_capital_quarantine_policy.md",
            "High",
            "Pseudo capital could leak into drafted-only buckets if not named.",
            "Draft-capital bucket gate",
            "Missing draft capital remains Not enough information, not zero.",
        ),
        status_row(
            "RO-003",
            "historical_labels",
            "Partition Outcome V2, local RotoWire/model_v4, and future nflverse player_stats labels.",
            WAIT,
            "Outcome V2 labels and local display-only labels both exist; no refresh-health packet landed.",
            "partial",
            "label_source_partition_policy.md",
            "High",
            "nflverse player_stats sidecar needs refresh-health receipts before implementation.",
            "Label-source specification gate",
            "Labels remain targets/evaluation only and never input features.",
        ),
        status_row(
            "RO-004",
            "feature_policy",
            "Publish Gate E feature manifest and downgrade broader replay-service features.",
            "SAFE_NOW",
            "Replay service has nine fields; Gate E allowed six non-leaky features.",
            "yes",
            "gate_e_feature_policy_manifest.csv",
            "High",
            "Feature expansion needs a later model gate.",
            "Gate E feature approval",
            "All model_use_allowed and training_allowed values remain false.",
        ),
        status_row(
            "RO-005",
            "gate_e_readiness",
            "Keep Gate E limited to drafted-only review-only R&D.",
            "NEED_MODEL_GATE",
            "Gate E validation passed review-only, but this lane does not train or tune.",
            "partial",
            "next_safe_upgrade_plan.md",
            "High",
            "Any tuning, scoring, calibration promotion, or current output requires another prompt.",
            "Gate E model gate",
            "No current-player probabilities created.",
        ),
        status_row(
            "RO-006",
            "gate_f_readiness",
            "Keep Gate F partial, display-only, and review-only.",
            "SAFE_NOW",
            "V5 display matrix exists, but remains non-app-wired and partial.",
            "yes",
            "gate_f_display_artifact_policy.md",
            "High",
            "Display artifacts can be mistaken for production approval.",
            "Gate F display policy",
            "No active T12/T24/T36 outputs are approved.",
        ),
        status_row(
            "RO-007",
            "udfa_nondrafted",
            "Keep UDFA/non-drafted modeling blocked.",
            "BLOCKED",
            "Historical artifact has zero confirmed UDFA rows and current UDFA status is review-only.",
            "yes",
            "udfa_cfbd_blocker_update.md",
            "Very high",
            "Draft absence, rosters, depth charts, stats, and injuries cannot confirm UDFA.",
            "UDFA source-policy gate",
            "Current review-only UDFA decisions do not generalize to historical modeling.",
        ),
        status_row(
            "RO-008",
            "cfbd_identity",
            "Keep CFBD candidate rows review-only until human-approved identity links exist.",
            "BLOCKED",
            "CFBD identity rows remain review-required and not model/training allowed.",
            "yes",
            "udfa_cfbd_blocker_update.md",
            "Very high",
            "CFBD identity and production are not approved model input or training truth.",
            "CFBD identity approval gate",
            "No CFBD input promotion in this lane.",
        ),
        status_row(
            "RO-009",
            "source_policy",
            "Default refreshed nflverse datasets to review-only receipts.",
            WAIT,
            "The dataset-level refresh-health lane has no tracked landed packet on target.",
            "partial",
            "deep_research_intake_summary.md",
            "Medium",
            "Refresh outputs cannot automatically become source truth, model input, or training data.",
            "nflverse refresh-health gate",
            "Docs/specs only until refresh-health is green.",
        ),
        status_row(
            "RO-010",
            "gate_g",
            "Keep Gate G and Rankings wiring closed.",
            "BLOCKED",
            "No approval for Rankings wiring or app-facing rookie columns.",
            "yes",
            "gate_g_blocker_policy.md",
            "Very high",
            "Gate G needs explicit release authorization.",
            "Gate G release approval",
            "No app files changed.",
        ),
    ]


def status_row(
    finding_id: str,
    area: str,
    recommendation: str,
    classification: str,
    current_repo_status: str,
    implemented: str,
    output_path_or_test: str,
    guardrail_risk: str,
    blocker_reason: str,
    next_gate: str,
    notes: str,
) -> dict[str, str]:
    return {
        "finding_id": finding_id,
        "area": area,
        "recommendation": recommendation,
        "classification": classification,
        "current_repo_status": current_repo_status,
        "implemented_in_this_lane": implemented,
        "output_path_or_test": output_path_or_test,
        "guardrail_risk": guardrail_risk,
        "blocker_reason": blocker_reason,
        "next_gate": next_gate,
        "notes": notes,
    }


def build_admission_rows() -> list[dict[str, str]]:
    return [
        admission_row(
            "DAG-001",
            "positive_draft_picks_admission",
            "nflverse draft_picks",
            "Exact positive draft-pick evidence with real draft year, round, and pick.",
            "Eligible for drafted-only review coverage.",
            "No drafted-only admission from any other source alone.",
            NOT_ENOUGH,
            "yes",
        ),
        admission_row(
            "DAG-002",
            "identity_enrichment_not_admission",
            "ff_playerids, rosters, weekly rosters, Sleeper/NWR IDs",
            "May support identity context after drafted evidence exists.",
            "Enrichment only.",
            "Cannot override draft_picks or admit a drafted row.",
            NOT_ENOUGH,
            "yes",
        ),
        admission_row(
            "DAG-003",
            "draft_absence_not_udfa",
            "draft_picks search result",
            "Absence may be documented only as absence from draft_picks.",
            "not_found_in_draft_picks_needs_review.",
            "Cannot become confirmed_udfa, source truth, model input, or clean miss.",
            NOT_ENOUGH,
            "yes",
        ),
        admission_row(
            "DAG-004",
            "real_nfl_rounds_only",
            "draft_picks",
            "Modern drafted path round must be 1 through 7 with a real pick.",
            "Draft-capital bucket may use true round bucket for review reporting.",
            "Round 8, missing, unknown, or pseudo rows are blocked from drafted buckets.",
            NOT_ENOUGH,
            "yes",
        ),
        admission_row(
            "DAG-005",
            "pseudo_capital_quarantine",
            "review-only display artifacts",
            "Pseudo draft-capital state is explicitly labeled review-only.",
            "Display-only quarantine status.",
            "Cannot be converted to draft capital, model feature, or admission evidence.",
            NOT_ENOUGH,
            "yes",
        ),
        admission_row(
            "DAG-006",
            "no_zero_fill",
            "all intake artifacts",
            "Missing round, pick, status, label, or feature remains missing.",
            NOT_ENOUGH,
            "Zero, false, healthy, low-risk, not drafted, or no-hit inferred values.",
            NOT_ENOUGH,
            "yes",
        ),
    ]


def admission_row(
    rule_id: str,
    rule_name: str,
    source: str,
    required_condition: str,
    allowed_result: str,
    blocked_result: str,
    missing_behavior: str,
    test_required: str,
) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "source": source,
        "required_condition": required_condition,
        "allowed_result": allowed_result,
        "blocked_result": blocked_result,
        "missing_data_behavior": missing_behavior,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "test_required": test_required,
    }


def build_feature_rows() -> list[dict[str, str]]:
    rows = [
        replay_feature("draft_capital_score", "historical_rookie_replay_service", "no"),
        replay_feature("age_trajectory_score", "historical_rookie_replay_service", "no"),
        replay_feature("production_score", "historical_rookie_replay_service", "no"),
        replay_feature("efficiency_score", "historical_rookie_replay_service", "no"),
        replay_feature("target_earning_score", "historical_rookie_replay_service", "no"),
        replay_feature("rushing_profile_score", "historical_rookie_replay_service", "no"),
        replay_feature("receiving_role_score", "historical_rookie_replay_service", "no"),
        replay_feature("athleticism_score", "historical_rookie_replay_service", "no"),
        replay_feature("lve_position_fit_score", "historical_rookie_replay_service", "no"),
    ]
    for name in (
        "draft_year",
        "draft_round",
        "draft_pick",
        "draft_capital_bucket",
        "rookie_class_year",
        "position",
    ):
        rows.append(
            feature_row(
                name,
                "Gate E six-feature cap / drafted-only review artifacts",
                "no",
                "yes",
                "yes",
                "yes",
                "yes",
                "false",
                "review-only receipts; no model/training promotion in this lane",
                "Gate E model-use approval",
                "Named in the existing six-feature Gate E cap.",
            )
        )
    for name, source, predraft, postdraft, blocked, gate, notes in (
        (
            "overall_pick",
            "nflverse draft_picks / repaired artifacts",
            "yes",
            "yes",
            "false",
            "Gate D/Gate E refresh",
            "Useful factual draft context, but not one of the six named Gate E features here.",
        ),
        (
            "draft_team",
            "nflverse draft_picks",
            "yes",
            "yes",
            "false",
            "Feature approval gate",
            "Drafted team may be display context; model use remains closed.",
        ),
        (
            "combine measurements",
            "nflverse combine",
            "pending",
            "yes",
            "false",
            WAIT,
            "Requires refresh-health receipts and later feature approval.",
        ),
        (
            "CFBD production",
            "CFBD review artifacts",
            "pending",
            "no",
            "yes",
            "CFBD identity approval gate",
            "Candidate-only until human-approved identity and source policy exist.",
        ),
        (
            "CFBD transfer/team timeline",
            "CFBD review artifacts",
            "pending",
            "no",
            "yes",
            "CFBD identity approval gate",
            "Timeline risk remains review-only.",
        ),
        (
            "recruiting context",
            "missing or unapproved source",
            "pending",
            "no",
            "yes",
            "Source-policy gate",
            "Not approved for this lane.",
        ),
        (
            "age",
            "tracked age/identity artifacts if available",
            "pending",
            "no",
            "false",
            "Feature approval gate",
            "Age can be factual context, but not promoted here.",
        ),
        (
            "depth_chart_rank",
            "depth charts",
            "no",
            "yes",
            "yes",
            WAIT,
            "Post-draft opportunity context only; not historical pre-draft model input.",
        ),
        (
            "roster status",
            "rosters / weekly rosters",
            "no",
            "yes",
            "yes",
            WAIT,
            "Cannot confirm UDFA or serve as pre-draft feature.",
        ),
        (
            "snap counts",
            "nflverse snap_counts",
            "no",
            "yes",
            "yes",
            WAIT,
            "Future participation is leakage for pre-draft predictions.",
        ),
        (
            "injury context",
            "nflverse injuries",
            "no",
            "yes",
            "yes",
            WAIT,
            "Post-draft status context only unless a later gate approves a point-in-time use.",
        ),
        (
            "Outcome V2 labels",
            "Outcome V2 exact verified first-down labels",
            "no",
            "yes",
            "yes",
            "Label-source gate",
            "Targets/evaluation only; never input features.",
        ),
        (
            "player_stats",
            "nflverse player_stats",
            "no",
            "yes",
            "yes",
            WAIT,
            "Future sidecar comparison only until label-spec approval.",
        ),
        (
            "RotoWire display-only labels",
            "local model_v4 display-only path",
            "no",
            "yes",
            "yes",
            "Source-policy gate",
            "Local/vendor-derived display comparison only.",
        ),
        (
            "DynastyProcess/ADP/market data",
            "market sources",
            "no",
            "no",
            "yes",
            "Blocked source policy",
            "Market and ADP inputs remain blocked.",
        ),
        (
            "Gmail/vendor/manual notes",
            "private/vendor/manual notes",
            "no",
            "no",
            "yes",
            "Blocked source policy",
            "Private/vendor/manual notes are not model inputs.",
        ),
    ):
        rows.append(
            feature_row(
                name,
                source,
                "no",
                "pending",
                predraft,
                postdraft,
                "yes",
                blocked,
                "downgrade_to_review_only_or_blocked",
                gate,
                notes,
            )
        )
    return rows


def replay_feature(name: str, source: str, approved: str) -> dict[str, str]:
    return feature_row(
        name,
        source,
        "yes",
        approved,
        "pending",
        "no",
        "yes",
        "false",
        "downgrade_to_review_only_unless_feature_gate_approves",
        "Gate E feature approval",
        "Replay contract feature is not automatically part of the six-feature Gate E cap.",
    )


def feature_row(
    feature_name: str,
    source: str,
    replay: str,
    gate_e: str,
    predraft: str,
    postdraft: str,
    review_only: str,
    blocked_leakage: str,
    downgrade: str,
    required_gate: str,
    notes: str,
) -> dict[str, str]:
    return {
        "feature_name": feature_name,
        "current_source_or_service": source,
        "appears_in_replay_contract": replay,
        "approved_in_gate_e_six_feature_cap": gate_e,
        "pre_draft_allowed": predraft,
        "post_draft_allowed": postdraft,
        "review_only": review_only,
        "model_use_allowed": "false",
        "training_allowed": "false",
        "blocked_leakage": blocked_leakage,
        "downgrade_behavior": downgrade,
        "required_gate": required_gate,
        "notes": notes,
    }


def build_label_rows() -> list[dict[str, str]]:
    return [
        label_row(
            "Outcome V2 exact verified first-down labels",
            r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\ "
            "(generated outside git) plus tracked coverage docs",
            "available_as_review_only_historical_target",
            "historical_review_only",
            "false",
            "true",
            "false",
            "false",
            "none_for_existing_review_docs",
            "Not promoted to training/source truth.",
            "Label-source approval gate",
        ),
        label_row(
            "model_v4 RotoWire-derived labels",
            "src/services/model_v4_rookie_outcome_label_service.py / local_exports source path",
            "display_only_local_vendor_review_comparison",
            "false",
            "false",
            "true",
            "true",
            "false",
            "blocked_local_vendor_source",
            "Underlying rows are local/vendor-derived and not approved truth.",
            "Source-policy gate",
        ),
        label_row(
            "nflverse player_stats-derived sidecar labels",
            "nflverse player_stats",
            WAIT,
            "false",
            "false",
            "true",
            "true",
            "false",
            WAIT,
            "Requires refresh-health, parity checks, and label-spec approval.",
            "nflverse refresh-health then label-source gate",
        ),
        label_row(
            "CFBD production context",
            "CFBD review artifacts",
            "review_only_context",
            "false",
            "false",
            "true",
            "true",
            "false",
            "none",
            "College production is not NFL outcome truth.",
            "CFBD identity/source approval gate",
        ),
        label_row(
            "app display gaps or missing fields",
            "app/display artifacts",
            "blocked",
            "false",
            "false",
            "false",
            "false",
            "false",
            "none",
            "Missing display data cannot become a miss, zero, false, or no-hit label.",
            "Blocked",
        ),
    ]


def label_row(
    family: str,
    source: str,
    status: str,
    allowed_target: str,
    allowed_feature: str,
    review_only: str,
    display_only: str,
    source_truth: str,
    refresh_dependency: str,
    blocker: str,
    next_gate: str,
) -> dict[str, str]:
    return {
        "label_family": family,
        "source_path_or_dataset": source,
        "current_status": status,
        "allowed_as_label_target": allowed_target,
        "allowed_as_feature": allowed_feature,
        "review_only": review_only,
        "display_only": display_only,
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": source_truth,
        "refresh_dependency": refresh_dependency,
        "blocker_reason": blocker,
        "next_gate": next_gate,
    }


def write_docs(output_root: Path, counts: dict[str, int | str]) -> None:
    docs = {
        "artifact_manifest.md": artifact_manifest(counts),
        "deep_research_intake_summary.md": deep_research_intake_summary(),
        "drafted_only_admission_gate_contract.md": drafted_only_admission_contract(),
        "synthetic_draft_capital_quarantine_policy.md": quarantine_policy(),
        "label_source_partition_policy.md": label_source_partition_policy(),
        "historical_replay_leakage_guardrail.md": replay_leakage_guardrail(),
        "depth_chart_source_reaudit.md": depth_chart_reaudit(counts),
        "udfa_cfbd_blocker_update.md": udfa_cfbd_blocker_update(counts),
        "gate_f_display_artifact_policy.md": gate_f_policy(counts),
        "gate_g_blocker_policy.md": gate_g_policy(),
        "next_safe_upgrade_plan.md": next_safe_upgrade_plan(),
        "codex_final_work_order.md": codex_final_work_order(),
        "merge_safety_report.md": merge_safety_report(),
        "README.md": readme(),
    }
    for name, text in docs.items():
        (output_root / name).write_text(text.strip() + "\n", encoding="utf-8")


def artifact_manifest(counts: dict[str, int | str]) -> str:
    return f"""
# Artifact Manifest

Verdict: `{VERDICT}`

Branch: `{BRANCH}`

Worktree: `{WORKTREE}`

Base HEAD checked before implementation: `{BASE_HEAD}`

This packet implements the safe-now policy/spec portion of the Rookie Outcomes drafted-only safe-upgrade lane. It does not train, tune, score, app-wire, release, or approve active rookie outcome columns.

## Inputs Used

| Input | Purpose | Review-only status |
|---|---|---|
| `NWR_DEEP_RESEARCH_05_ROOKIE_OUTCOMES_20260630.md` from the handoff zip | Findings and recommended classifications | Research input only |
| `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv` | Entry-status counts and drafted-only boundary | review-only |
| `docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv` | Drafted-only coverage counts | review-only |
| `docs/hq/rookie_outcomes/udfa_review_application_v1_20260630/rookie_display_artifact_v5_coverage_matrix.csv` | Current display/UDFA status counts | review-only/display-only |
| `docs/hq/rookie_model/rookie_source_availability_reconciliation_20260630/source_availability_matrix.csv` | Depth-chart and UDFA/CFBD source-policy status | review-only policy |

## Output Artifacts

| Artifact | Rows | Purpose | Status |
|---|---:|---|---|
| `rookie_outcomes_safe_upgrade_status_matrix.csv` | 10 | Classifies RO-001 through RO-010 recommendations | review-only/spec |
| `drafted_only_admission_gate_contract.csv` | 6 | Machine-readable drafted-only gate contract | review-only/spec |
| `gate_e_feature_policy_manifest.csv` | 31 | Reconciles the nine replay-service fields, six Gate E features, and blocked candidates | review-only/spec |
| `label_source_partition_matrix.csv` | 5 | Separates Outcome V2, model_v4/RotoWire, nflverse sidecar, CFBD, and display gaps | review-only/spec |
| `artifact_manifest.md` | n/a | This manifest | docs-only |
| `deep_research_intake_summary.md` | n/a | Research intake and classification | docs-only |
| `drafted_only_admission_gate_contract.md` | n/a | Human-readable admission gate | docs-only |
| `synthetic_draft_capital_quarantine_policy.md` | n/a | Round/pseudo-capital quarantine | docs-only |
| `label_source_partition_policy.md` | n/a | Label-source policy | docs-only |
| `historical_replay_leakage_guardrail.md` | n/a | Replay leakage controls | docs-only |
| `depth_chart_source_reaudit.md` | n/a | Current depth-chart source status | docs-only |
| `udfa_cfbd_blocker_update.md` | n/a | UDFA/CFBD blockers | docs-only |
| `gate_f_display_artifact_policy.md` | n/a | Gate F display-only policy | docs-only |
| `gate_g_blocker_policy.md` | n/a | Gate G blocker policy | docs-only |
| `next_safe_upgrade_plan.md` | n/a | Safe/WAIT/model-gate/blocked plan | docs-only |
| `codex_final_work_order.md` | n/a | Work-order receipt | docs-only |
| `merge_safety_report.md` | n/a | Guardrail merge receipt | docs-only |
| `README.md` | n/a | Folder overview | docs-only |

## Key Counts

- Historical entry-status rows: `{counts["entry_total"]}`
- Historical drafted rows: `{counts["entry_drafted"]}`
- Historical likely UDFA / needs-review rows: `{counts["entry_likely_udfa"]}`
- Historical confirmed UDFA rows: `{counts["entry_confirmed_udfa"]}`
- Drafted-only review audit rows: `{counts["drafted_rows"]}`
- Drafted rows with any label linkage: `{counts["drafted_any_label"]}`
- Rookie-year labels: `{counts["drafted_rookie_year"]}`
- 2Y labels: `{counts["drafted_2y"]}`
- 3Y labels: `{counts["drafted_3y"]}`
- 5Y labels: `{counts["drafted_5y"]}`
- Current display V5 rows: `{counts["display_rows"]}`
- V5 review-only display-field rows: `{counts["display_review_fields"]}`
- V5 confirmed UDFA review-only status rows: `{counts["display_udfa_status_only"]}`
- V5 Not enough information rows: `{counts["display_not_enough"]}`
- V5 wrong-universe blocked rows: `{counts["display_wrong_universe"]}`

## What This Packet Approves

- Drafted-only review-only policy/spec work.
- Positive `draft_picks` evidence as the drafted-only admission contract.
- Conservative display-only/review-only label-source partitioning.
- Guardrail tests for no model/training/source-truth promotion.

## What This Packet Does Not Approve

- Active rookie probabilities.
- Gate G.
- Rankings, Player Compare, Live Draft Room, or Gate F/G app behavior.
- Model/training/source-truth use.
- UDFA modeling or UDFA inference from draft absence.
- CFBD as model input or training truth.
- Fake round 8, fake T12/T24/T36, or missing-as-zero output.
"""


def deep_research_intake_summary() -> str:
    return f"""
# Deep Research Intake Summary

The handoff report concludes that Rookie Outcomes is not production-ready but may continue as drafted-only, review-only policy and readiness work. This lane implements safe policy artifacts and tests only.

## Accepted Safe-Now Changes

- RO-001: drafted-only admission is defined as positive `draft_picks` evidence only.
- RO-002: synthetic round/pseudo draft capital is quarantined outside drafted-only buckets.
- RO-004: Gate E feature-policy manifest now names the replay-service feature contract and the six Gate E features.
- RO-006: Gate F is restated as partial display-only/review-only.
- RO-010: Gate G remains closed.

## {WAIT} Items

- RO-003: nflverse `player_stats` sidecar labels.
- RO-009: dataset-level nflverse receipts for `draft_picks`, `combine`, `player_stats`, `rosters`, `weekly_rosters`, `ff_playerids`, `depth_charts`, `snap_counts`, and `injuries`.
- Depth-chart row counts, teams, positions, and parseable rank/order from refreshed nflverse data.

The target branch contains older refresh machinery, but no tracked merged refresh-health packet proving dataset-level receipts for this lane. Therefore refresh-dependent implementation is held.

## NEED_MODEL_GATE Items

- Gate E model R&D refresh, tuning, calibration promotion, or current-player scoring.
- Any expansion beyond the six named Gate E features.
- Any promotion of labels from evaluation targets to training truth.
- Any use of combine/depth/roster/snap/injury fields as model inputs.

## BLOCKED Items

- UDFA/non-drafted modeling.
- CFBD model input or training truth.
- Gate G, Rankings wiring, app-facing rookie columns, or hidden sort behavior.
- FootballDB/vendor/Gmail/RotoWire/FantasyPros/private source ingestion.

## Repo-State Conflicts Resolved

- Label-source split is resolved by naming Outcome V2 as review-only historical target/evaluation, model_v4 RotoWire-derived labels as local display-only comparison, and nflverse player_stats as a future sidecar only.
- Feature-policy split is resolved by treating the replay service's nine fields as review-only/replay-contract fields unless a later model gate approves them; only six Gate E names are marked as part of the current cap.
- Source-policy split is resolved by defaulting all new nflverse refresh outputs to review-only receipts until a later gate.

## Stale-Source Conclusions

The tracked source reconciliation still reports no approved populated tracked depth-chart data: the nflverse depth-chart item is schema-only with zero rows, and RotoWire depth-chart material remains local/vendor-blocked. Because the refresh-health lane is not landed as a tracked packet here, the prior populated-depth conclusion is not superseded.
"""


def drafted_only_admission_contract() -> str:
    return """
# Drafted-Only Admission Gate Contract

Drafted-only Rookie Outcomes work is admitted only by positive `draft_picks` evidence. A player must have a real draft year, real NFL draft round, and real pick/overall pick from an approved draft-pick source to enter drafted-only review coverage.

Other datasets may enrich identity and status after the drafted row exists. `ff_playerids`, roster data, weekly rosters, depth charts, player stats, snap counts, injuries, Sleeper/NWR IDs, or CFBD candidate rows cannot admit a drafted row by themselves.

Draft absence cannot imply UDFA. Absence from draft-pick rows can be documented as `not_found_in_draft_picks_needs_review`, but it cannot create `confirmed_udfa`, clean draft capital, a model feature, or training truth.

Real NFL draft rounds only are admitted in the modern drafted path. Synthetic round 8, missing round, pseudo-capital, unknown status, or review-only UDFA status must stay outside drafted-only model buckets.

All outputs remain:

- `review_only=true`
- `model_use_allowed=false`
- `training_allowed=false`

Missing draft fields remain `Not enough information`; they are never zero, false, healthy, low-risk, undrafted, or a miss.
"""


def quarantine_policy() -> str:
    return """
# Synthetic Draft-Capital Quarantine Policy

Synthetic or pseudo draft capital includes `round 8`, UDFA-as-round, inferred draft capital, missing-as-zero, display-only pseudo buckets, and any row not backed by positive `draft_picks` round/pick evidence.

The drafted path allows only valid NFL draft rounds and picks from draft-pick evidence. Pseudo-capital may appear only as display-only/review-only status, and only when labeled as such.

Pseudo-capital cannot:

- feed drafted-only model buckets;
- become draft capital;
- admit a player into drafted-only models;
- be treated as Round 8 in modern NFL data;
- substitute for missing draft capital;
- become a zero, false, or low-risk value.

UDFA/undrafted is a separate status area. If UDFA status is not confirmed by approved source policy, it remains review-needed or `Not enough information`.
"""


def label_source_partition_policy() -> str:
    return f"""
# Label Source Partition Policy

Outcome labels and display comparisons are separated by family.

## Outcome V2 Exact Verified First-Down Labels

These are the current historical label/evaluation target for drafted-only review artifacts. They remain review-only unless a later gate explicitly promotes them. They may be used to audit historical outcome windows, but they are not input features.

## model_v4 RotoWire-Derived Labels

The model_v4 label path is local/vendor-derived display comparison material. It is not source truth, model input, or training truth. It remains display-only and local-path dependent.

## nflverse player_stats-Derived Labels

This is a future sidecar comparison candidate only. Because the refresh-health packet has not landed on the target branch, this family is `{WAIT}`. Even after refresh-health, player_stats-derived labels need parity checks and an explicit label-spec gate.

## CFBD

CFBD production is not NFL outcome truth. It remains identity/college context only and requires human-approved identity links before any stronger use.

## Missing Labels and Incomplete Windows

Missing labels are `Not enough information`. Incomplete future windows are right-censored. Neither becomes a failure, zero, false, no-hit label, or active rookie probability.
"""


def replay_leakage_guardrail() -> str:
    return """
# Historical Replay Leakage Guardrail

The existing historical replay service must preserve its leakage controls:

- ranking inputs are pre-NFL/as-of-draft only;
- outcome joins happen after ranking;
- changing an outcome file must not change ranking order;
- `future_nfl_stats_used=false`;
- top-5/top-10/top-20 hit rates are review/evaluation only;
- no current rookie probabilities are produced.

Existing tests already exercise these controls in `tests/test_historical_rookie_replay_service.py`, including ranking-order invariance when outcome rows change and feature receipts excluding outcome fields.

This lane adds policy tests to ensure the new Gate E feature manifest keeps Outcome V2 labels, player_stats, snap counts, injuries, roster status, and depth-chart rank out of model/training use.
"""


def depth_chart_reaudit(counts: dict[str, int | str]) -> str:
    return f"""
# Depth-Chart Source Re-Audit

Question: does approved tracked populated depth-chart data exist now?

Answer: no approved tracked populated depth-chart rows are present in the current target branch for this lane.

## Current Tracked Source Facts

| Source | Path | Row count/status | Policy |
|---|---|---:|---|
| nflverse depth chart weekly template | `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_depth_chart_weekly.csv` | `{counts["depth_chart_template_row_count"]}` | schema-only / pending |
| RotoWire May 22 depth-chart snapshot documentation | `docs/model_v4/ROTOWIRE_DEPTH_CHART_MAY22_SNAPSHOT.md` | `{counts["rotowire_depth_documented_count"]}` | documentation-only; underlying local/vendor rows blocked |
| model_v4 depth chart snapshot service | `src/services/model_v4_depth_chart_snapshot_service.py` | code-only | blocked local/vendor source |

## Required Answers

- Teams/positions covered: `{WAIT}` for nflverse refresh output; not available from tracked populated data here.
- Player IDs present: `{WAIT}` for refresh output.
- Depth rank/order parseable: `{WAIT}` for refresh output.
- Current-only or point-in-time historical: `{WAIT}` for refresh output.
- Source policy status: review-only pending for public nflverse refresh receipts; blocked for local/vendor/RotoWire rows.
- Usable for review-only opportunity watchlist: not from current tracked populated rows; possible only after refresh-health green and source-policy review.
- Usable for historical modeling: no.
- RotoWire, local_exports, and vendor data: blocked.
- Previous zero-row conclusion superseded: no, not on this target branch.
"""


def udfa_cfbd_blocker_update(counts: dict[str, int | str]) -> str:
    return f"""
# UDFA and CFBD Blocker Update

UDFA modeling remains blocked. The historical entry-status artifact contains `{counts["entry_confirmed_udfa"]}` confirmed UDFA rows and `{counts["entry_likely_udfa"]}` likely UDFA / needs-review rows. Current-rookie review-only UDFA decisions do not become historical source truth, model input, or training truth.

Draft absence cannot confirm UDFA. Player stats, rosters, weekly rosters, depth charts, snap counts, injuries, games, starts, awards, career length, and fantasy outcomes cannot confirm UDFA.

CFBD remains review-only unless human-approved identity links exist. CFBD identity candidates, production context, transfer/timeline context, and school/position fields may support review packets only. They are not model input, training truth, source truth, or a way to bypass identity review.

Required future gates:

- UDFA source-policy gate with direct approved evidence.
- CFBD human identity approval and production/source approval.
- Separate model gate before any model/training use.
"""


def gate_f_policy(counts: dict[str, int | str]) -> str:
    return f"""
# Gate F Display Artifact Policy

Gate F may remain a partial review-only display artifact only.

Current V5 display audit:

- Total rows: `{counts["display_rows"]}`
- Review-only display-field rows: `{counts["display_review_fields"]}`
- Confirmed UDFA review-only status rows: `{counts["display_udfa_status_only"]}`
- `Not enough information` rows: `{counts["display_not_enough"]}`
- Wrong-universe blocked rows: `{counts["display_wrong_universe"]}`

Gate F does not approve:

- active probabilities;
- fake T12/T24/T36 outputs;
- no active T12/T24/T36 outputs are approved;
- model/training use;
- Rankings, Player Compare, Live Draft, or Gate G app wiring;
- hidden sorting/ranking behavior.

Missing or partial evidence must stay visible as `Not enough information`.
"""


def gate_g_policy() -> str:
    return """
# Gate G Blocker Policy

Gate G remains closed.

Blocked:

- Rankings integration;
- app-facing rookie columns;
- production model use;
- source-truth promotion;
- active rookie probabilities;
- hidden sorting or ranking changes;
- Player Compare, Live Draft Room, or Gate F/G behavior changes.

Gate G can reopen only with explicit user approval and a separate release lane after coverage, validation, feature-policy, source-policy, and UI risk are all green.
"""


def next_safe_upgrade_plan() -> str:
    return f"""
# Next Safe Upgrade Plan

## A. Implemented / Safe Now

- Drafted-only admission contract.
- Synthetic draft-capital quarantine policy.
- Gate E feature manifest.
- Label-source partition policy.
- Historical replay leakage guardrail documentation.
- Gate F/G blocker policies.
- Focused guardrail tests.

## B. Waiting For nflverse Refresh Health Green

- Dataset-level refresh receipts for draft_picks, combine, player_stats, rosters, weekly_rosters, ff_playerids, depth_charts, snap_counts, and injuries.
- Depth-chart row counts, teams, positions, IDs, and parseable depth order.
- nflverse player_stats sidecar label comparison.

Classification: `{WAIT}`.

## C. Needs Model Gate

- Any Gate E refresh or model tuning.
- Any use of combine, depth, roster, snap, injury, age, or broader replay features as model inputs.
- Any promotion of label targets to training truth.

## D. Blocked

- UDFA/non-drafted modeling.
- CFBD model input or training truth.
- Gate G / Rankings wiring.
- Vendor/Gmail/RotoWire/FantasyPros/FootballDB/private/raw source ingestion.

## E. Recommended Next Branch

`work/lane-nflverse-refresh-health-20260630` should complete first if the next work needs refreshed public datasets. Otherwise, the next safe Rookie Outcomes lane should be a review-only feature-gate approval packet for the six Gate E features and any proposed additions.
"""


def codex_final_work_order() -> str:
    return f"""
# NWR Rookie Outcomes Drafted-Only / Feature Policy Safe Upgrade Lane

Branch: `{BRANCH}`

Worktree: `{WORKTREE}`

Base HEAD: `{BASE_HEAD}`

Final verdict: `{VERDICT}`

## Patched

- Created the drafted-only/feature-policy safe-upgrade packet under this folder.
- Added machine-readable matrices for status, admission, features, and label-source partitioning.
- Added guardrail documentation for synthetic draft capital, replay leakage, UDFA/CFBD blockers, Gate F, and Gate G.
- Added tests that enforce conservative flags and blocked paths.

## Still Blocked

- nflverse dataset-dependent implementation until refresh-health green.
- UDFA modeling.
- CFBD model/training use.
- model tuning/training/scoring.
- Gate G and app wiring.

## Merge Readiness

This packet is safe to merge as review-only docs/spec/tests if checks pass. It does not alter runtime behavior.
"""


def merge_safety_report() -> str:
    return """
# Merge Safety Report

Confirmed by lane design:

- no app files changed;
- no Rankings, Draft Room, Player Compare, Gate F, or Gate G behavior changed;
- no model outputs changed;
- no production refresh behavior changed;
- no source-truth behavior changed;
- no pinned snapshots changed;
- no `latest_candidate` or `latest_approved` changed;
- no Frozen Final Draft Board, rank, tier, or `final_board_rank` mutation;
- no protected/raw/private paths tracked;
- no secrets tracked;
- no `local_exports` or vendor files tracked.

All new policy and matrix rows remain review-only/spec/test-only. No row is marked model-use or training-use allowed.
"""


def readme() -> str:
    return """
# Rookie Outcomes Drafted-Only / Feature Policy Safe Upgrade

This folder is a review-only policy/spec packet for the Rookie Outcomes lane. It implements safe drafted-only admission and feature/source policy documentation while keeping all release gates closed.

This packet is not a model-training lane, not a probability lane, and not an app-wiring lane.

Core verdict: `YELLOW_DRAFTED_ONLY_FEATURE_POLICY_SAFE_UPGRADE`.
"""


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()
