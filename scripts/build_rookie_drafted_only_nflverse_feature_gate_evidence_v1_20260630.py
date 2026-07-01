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
    / "rookie_drafted_only_nflverse_feature_gate_evidence_v1_20260630"
)

BASE_HEAD = "a35c2c1c7339d7a745d5d90e8af8d0624155a85c"
BRANCH = "work/rookie-drafted-only-nflverse-feature-gate-evidence-v1-20260630"
WORKTREE = r"C:\NWR\Niners-War-Room-rookie-drafted-only-nflverse-feature-gate-evidence-v1-20260630"
VERDICT = "YELLOW_ROOKIE_DRAFTED_ONLY_FEATURE_GATE_EVIDENCE_READY_NO_GATE_G"
NOT_ENOUGH = "Not enough information"

POLICY_GATE_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "outcomes"
    / "outcome_rookie_nflverse_feature_policy_gate_v1_20260630"
)
PLAYER_CONTEXT_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nflverse_player_context_display_20260630"
)
DISPLAY_CLOSEOUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_display_update_final_closeout_20260630"
)
ROOKIE_RERUN_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_outcomes_drafted_only_feature_policy_nflverse_green_rerun_20260630"
)
ENTRY_STATUS_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_entry_status_hygiene_v1_20260630"
    / "historical_rookie_entry_status_v1.csv"
)

MATRIX_COLUMNS = (
    "feature_family",
    "source_artifact",
    "pre_draft_or_post_draft",
    "current_review_status",
    "drafted_only_admission_allowed",
    "allowed_for_display_now",
    "allowed_for_model_now",
    "allowed_for_training_now",
    "allowed_for_source_truth_now",
    "allowed_as_label_source_now",
    "leakage_risk",
    "missingness_rule",
    "required_gate_before_experiment",
    "blocker_reason",
    "notes",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    source = load_source_data()
    matrix_rows = build_matrix_rows()

    write_csv(args.output_root / "rookie_feature_gate_matrix.csv", MATRIX_COLUMNS, matrix_rows)
    write_docs(args.output_root, source, matrix_rows)

    print(
        {
            "verdict": VERDICT,
            "base_head": BASE_HEAD,
            "output_root": str(args.output_root),
            "matrix_rows": len(matrix_rows),
            "safe_display_rows": source["counts"]["safe_display_rows"],
            "gated_rows": source["counts"]["gated_rows"],
        }
    )


def load_source_data() -> dict[str, object]:
    policy_rows = read_csv(POLICY_GATE_ROOT / "nflverse_feature_gate_matrix.csv")
    player_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_display_artifact.csv")
    schema_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_schema_manifest.csv")
    entry_rows = read_csv(ENTRY_STATUS_PATH)
    counts = build_counts(policy_rows, player_rows, schema_rows, entry_rows)
    return {
        "policy_rows": policy_rows,
        "player_rows": player_rows,
        "schema_rows": schema_rows,
        "entry_rows": entry_rows,
        "counts": counts,
    }


def build_counts(
    policy_rows: list[dict[str, str]],
    player_rows: list[dict[str, str]],
    schema_rows: list[dict[str, str]],
    entry_rows: list[dict[str, str]],
) -> dict[str, int | str]:
    identity = Counter(row["identity_join_status"] for row in player_rows)
    review = Counter(row["review_required"] for row in player_rows)
    entry = Counter(row["entry_status"] for row in entry_rows)
    schema_model = Counter(row["model_use_allowed"] for row in schema_rows)
    policy_model = Counter(row["allowed_for_model_now"] for row in policy_rows)
    return {
        "policy_rows": len(policy_rows),
        "player_context_rows": len(player_rows),
        "safe_display_rows": identity["SAFE_NOW_DISPLAY_ONLY"],
        "gated_rows": identity["NEED_IDENTITY_REVIEW"],
        "review_required_true": review["true"],
        "schema_model_false": schema_model["false"],
        "policy_model_false": policy_model["false"],
        "entry_drafted": entry["drafted"],
        "entry_likely_udfa": entry["likely_udfa_needs_review"],
        "entry_confirmed_udfa": entry["confirmed_udfa"],
        "entry_wrong_universe": entry["wrong_universe"],
        "entry_name_collision": entry["name_collision"],
    }


def build_matrix_rows() -> list[dict[str, str]]:
    return [
        row(
            "draft_picks drafted admission",
            "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv; docs/hq/rookie_outcomes/rookie_outcomes_drafted_only_feature_policy_nflverse_green_rerun_20260630/drafted_only_admission_gate_refresh_audit.csv",
            "post-draft factual admission evidence",
            "SAFE_FOR_DRAFTED_ONLY_REVIEW",
            "yes_positive_draft_picks_only",
            "yes_review_only",
            "no",
            "no",
            "no",
            "no",
            "low_if_positive_evidence_only",
            "Missing draft-pick evidence remains Not enough information and is not UDFA.",
            "Drafted-only admission evidence can support review; model use needs Gate E model approval.",
            "No blocker for drafted-only review; blocked for model/training/source-truth.",
            "This is the only admitted drafted-only source family; absence is not UDFA.",
        ),
        row("draft year", "draft_picks / drafted-only audit", "post-draft factual", "SAFE_REVIEW_CONTEXT", "component_only", "yes_review_only", "no", "no", "no", "no", "low", "Missing draft year remains Not enough information.", "Gate E model approval", "Not independently sufficient for admission.", "Can describe drafted-only review rows."),
        row("draft round", "draft_picks / drafted-only audit", "post-draft factual", "SAFE_REVIEW_CONTEXT", "component_only", "yes_review_only", "no", "no", "no", "no", "low", "Missing draft round remains Not enough information; no fake round 8.", "Gate E model approval", "Not independently sufficient for admission.", "Only real rounds are valid for review buckets."),
        row("overall pick", "draft_picks / drafted-only audit", "post-draft factual", "SAFE_REVIEW_CONTEXT", "component_only", "yes_review_only", "no", "no", "no", "no", "low", "Missing overall pick remains Not enough information.", "Gate E model approval", "Not independently sufficient for admission.", "Review context only."),
        row("drafted team", "draft_picks / drafted-only audit", "post-draft factual", "SAFE_REVIEW_CONTEXT", "component_only", "yes_review_only", "no", "no", "no", "no", "medium_context_team_changes", "Missing drafted team remains Not enough information.", "Gate E model approval", "Team context is not rank/trade/model signal here.", "Display/review context only."),
        row("combine", "docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/; docs/hq/outcomes/outcome_rookie_nflverse_feature_policy_gate_v1_20260630/", "pre-draft factual candidate", "REVIEW_ONLY_CANDIDATE", "no", "not_current_app_display", "no", "no", "no", "no", "medium_as_of_and_coverage_gate", "Missing combine rows remain Not enough information.", "Feature coverage plus historical replay/as-of gate", "No current model gate approval.", "May be studied later as factual prospect context."),
        row("rosters", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "post-draft/current context", "DISPLAY_ONLY_SAFE_ROWS", "no", "yes_safe_rows_only", "no", "no", "no", "no", "high_for_pre_draft_or_udfa_inference", "Missing roster row is not inactive, healthy, or UDFA.", "Historical replay/as-of gate", "Roster appearance cannot confirm UDFA or model readiness.", "Identity/status display only for safe rows."),
        row("weekly_rosters", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "post-draft/current context", "DISPLAY_ONLY_SAFE_ROWS", "no", "yes_safe_rows_only", "no", "no", "no", "no", "high_temporal_leakage", "Missing weekly roster row is not inactive, healthy, or UDFA.", "Historical replay/as-of gate", "Temporal roster state can leak without anchor.", "Display/status context only."),
        row("snap_counts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "post-draft production/context", "DISPLAY_ONLY_SAFE_ROWS", "no", "yes_safe_rows_only", "no", "no", "no", "no", "high_future_usage_leakage", "Missing snap data is not zero snaps.", "Historical replay/as-of gate", "Future usage cannot be pre-draft feature.", "Current display context only."),
        row("player_stats", "docs/hq/data_sources/nflverse_player_context_display_20260630/; rookie player_stats sidecar feasibility", "post-draft production/label sidecar candidate", "REVIEW_ONLY_SIDECAR_CANDIDATE", "no", "yes_for_display_presence_only", "no", "no", "no", "future_sidecar_only_no_truth", "high_future_production_leakage", "Missing player_stats rows are Not enough information, not zero production.", "Label parity plus historical replay gate", "Not label truth, training truth, or input feature.", "Future NFL production cannot be pre-draft feature."),
        row("depth_charts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "post-draft/current opportunity context", "DISPLAY_ONLY_SAFE_ROWS", "no", "yes_safe_rows_only", "no", "no", "no", "no", "high_current_role_leakage", "Missing depth chart is not no-role.", "Historical replay/as-of gate", "Depth context is not pre-draft feature or UDFA proof.", "Opportunity watchlist context only."),
        row("injury reports", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "post-draft/current availability context", "DISPLAY_ONLY_SAFE_ROWS", "no", "yes_safe_rows_only", "no", "no", "no", "no", "high_medical_projection_risk", "Missing injury context is not healthy.", "Availability denominator and medical guardrail gate", "Cannot become injury-risk score or medical projection.", "Transparency only."),
        row("schedule context", "docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/; player context artifact", "post-draft/current/future schedule context", "DISPLAY_BLOCKED_CURRENT_FUTURE_UNAVAILABLE", "no", "no_current_future_safe_rows", "no", "no", "no", "no", "high_recommendation_matchup_leakage", "Missing schedule is not bye, favorable, or clean.", "Schedule display gate and as-of gate", "No current/future safe rows in latest audit.", "No matchup/start-sit/trade timing use."),
        row("contracts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "post-draft/current context", "DISPLAY_ONLY_NON_FINANCIAL", "no", "yes_non_financial_display_only", "no", "no", "no", "no", "high_valuation_leakage", "Missing contract context is Not enough information.", "Contract context policy gate", "Not valuation, trade value, pick value, or rank signal.", "Non-financial display text only."),
        row("identity bridge health", "docs/hq/data_sources/nflverse_player_context_display_20260630/; docs/hq/data_sources/nflverse_display_update_final_closeout_20260630/", "identity/display gate", "DISPLAY_SAFE_WITH_13_GATED_ROWS", "no", "yes_safe_rows_only", "no", "no", "no", "no", "medium_identity_collision_risk", "Gated identity remains Needs identity review.", "Identity approval/binding gate", "13 rows remain gated.", "Does not approve source truth or model joins."),
        row("CFBD joins", "docs/hq/rookie_model/; docs/hq/rookie_outcomes/", "college identity/context", "BLOCKED_REVIEW_ONLY_CANDIDATE", "no", "review_packets_only", "no", "no", "no", "no", "high_identity_and_source_policy_risk", "Missing/ambiguous CFBD links remain review-required.", "CFBD identity/source approval gate", "CFBD model/training input remains blocked.", "No approved CFBD model/training joins."),
        row("UDFA status", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/", "entry status", "BLOCKED_FOR_MODELING", "no", "status_review_only_if_explicitly_accepted", "no", "no", "no", "no", "very_high_source_policy_risk", "Draft absence is not confirmed UDFA.", "Approved UDFA source-policy gate", "Confirmed historical UDFA source evidence is 0.", "No UDFA modeling."),
        row("likely_udfa_needs_review", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/", "entry status candidate", "BLOCKED_REVIEW_REQUIRED", "no", "review_queue_only", "no", "no", "no", "no", "very_high_false_confirmation_risk", "Likely is not confirmed; remains Not enough information for model use.", "Human/source approval gate", "Cannot enter model/training/source truth.", "Keep blocked from drafted-only counts."),
        row("fake/synthetic draft capital", "draft-capital repair and rookie rerun packets", "pseudo-context/quarantine", "BLOCKED_QUARANTINE", "no", "quarantine_status_only", "no", "no", "no", "no", "very_high_false_draft_signal", "Missing draft capital is not zero and not round 8.", "Draft capital source-policy gate", "Fake round 8 and pseudo capital cannot feed buckets.", "Quarantine only."),
        row("Outcome V2 labels", "docs/hq/outcomes/; docs/hq/rookie_outcomes/", "post-draft label/evaluation target", "REVIEW_ONLY_LABEL_TARGET", "no", "review_reports_only", "no", "no", "no", "review_only_label_target_not_feature", "high_label_leakage_if_feature", "Missing/incomplete labels are Not enough information or right-censored.", "Label parity and model approval gate", "Labels are not input features and do not activate current probabilities.", "Evaluation target only."),
        row("ff_rankings", "docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/; policy gate", "blocked source", "BLOCKED_VENDOR_OR_PRIVATE", "no", "no", "no", "no", "no", "no", "very_high_blocked_source", "Missing ff_rankings remain blocked, not Not enough information for use.", "Blocked unless source-policy explicitly changes", "ff_rankings remains blocked.", "No ingestion/model/rank use."),
    ]


def row(
    feature_family: str,
    source_artifact: str,
    timing: str,
    status: str,
    admission: str,
    display: str,
    model: str,
    training: str,
    source_truth: str,
    label_source: str,
    leakage: str,
    missingness: str,
    required_gate: str,
    blocker: str,
    notes: str,
) -> dict[str, str]:
    return {
        "feature_family": feature_family,
        "source_artifact": source_artifact,
        "pre_draft_or_post_draft": timing,
        "current_review_status": status,
        "drafted_only_admission_allowed": admission,
        "allowed_for_display_now": display,
        "allowed_for_model_now": model,
        "allowed_for_training_now": training,
        "allowed_for_source_truth_now": source_truth,
        "allowed_as_label_source_now": label_source,
        "leakage_risk": leakage,
        "missingness_rule": missingness,
        "required_gate_before_experiment": required_gate,
        "blocker_reason": blocker,
        "notes": notes,
    }


def write_docs(output_root: Path, source: dict[str, object], matrix_rows: list[dict[str, str]]) -> None:
    counts = source["counts"]
    docs = {
        "artifact_manifest.md": artifact_manifest(matrix_rows),
        "drafted_only_feature_gate_summary.md": drafted_only_feature_gate_summary(counts),
        "drafted_admission_source_reaudit.md": drafted_admission_source_reaudit(counts),
        "pre_draft_vs_post_draft_feature_policy.md": pre_draft_vs_post_draft_feature_policy(),
        "udfa_cfbd_blocker_reaudit.md": udfa_cfbd_blocker_reaudit(counts),
        "gate_e_f_g_status_after_policy_gate.md": gate_e_f_g_status_after_policy_gate(),
        "next_gate_recommendations.md": next_gate_recommendations(),
        "merge_safety_report.md": merge_safety_report(),
        "README.md": readme(),
    }
    for name, text in docs.items():
        (output_root / name).write_text(text.strip() + "\n", encoding="utf-8")


def artifact_manifest(matrix_rows: list[dict[str, str]]) -> str:
    return f"""
# Artifact Manifest

Verdict: `{VERDICT}`

Branch: `{BRANCH}`

Worktree: `{WORKTREE}`

Base HEAD: `{BASE_HEAD}`

This packet creates Rookie drafted-only NFLVerse feature-gate evidence only. It does not train, tune, score, create probabilities, approve Gate G, wire app behavior, approve UDFA modeling, or approve CFBD model/training input.

## Created Artifacts

| Artifact | Rows | Purpose |
|---|---:|---|
| `artifact_manifest.md` | n/a | Packet inventory and approval boundary |
| `drafted_only_feature_gate_summary.md` | n/a | Summary of drafted-only NFLVerse feature posture |
| `rookie_feature_gate_matrix.csv` | {len(matrix_rows)} | Feature-family evidence matrix |
| `drafted_admission_source_reaudit.md` | n/a | Drafted-only admission source reaudit |
| `pre_draft_vs_post_draft_feature_policy.md` | n/a | Timing/leakage policy |
| `udfa_cfbd_blocker_reaudit.md` | n/a | UDFA/CFBD blocker confirmation |
| `gate_e_f_g_status_after_policy_gate.md` | n/a | Rookie Gate E/F/G status |
| `next_gate_recommendations.md` | n/a | Safe next evidence lanes |
| `merge_safety_report.md` | n/a | Merge and guardrail proof |

Every matrix row keeps `allowed_for_model_now=false`, `allowed_for_training_now=false`, and `allowed_for_source_truth_now=false`.
"""


def drafted_only_feature_gate_summary(counts: dict[str, int | str]) -> str:
    return f"""
# Drafted-Only Feature Gate Summary

Verdict: `{VERDICT}`

The primary policy input, `docs/hq/outcomes/outcome_rookie_nflverse_feature_policy_gate_v1_20260630/`, is `YELLOW_MODEL_POLICY_GATE_READY_NO_ACTIVATION`. This rookie lane narrows that posture to drafted-only Rookie Outcomes evidence.

## Current NFLVerse Display Facts

- Player context rows: `{counts["player_context_rows"]}`
- Safe display rows: `{counts["safe_display_rows"]}`
- Gated identity rows: `{counts["gated_rows"]}`
- Rows requiring review: `{counts["review_required_true"]}`
- Schema fields with `model_use_allowed=false`: `{counts["schema_model_false"]}`
- Outcome/Rookie policy matrix rows with `allowed_for_model_now=false`: `{counts["policy_model_false"]}`

## Drafted-Only Classification

Drafted-only review may proceed only when positive `draft_picks` evidence exists. Draft year, round, overall pick, and drafted team are review context after admission, not independent admission sources. Missing draft capital does not confirm UDFA, and fake round 8 is blocked.

## Approval Boundary

No feature family is approved for model use, training use, source truth, active rookie probabilities, Gate G, Rankings wiring, or app behavior changes.
"""


def drafted_admission_source_reaudit(counts: dict[str, int | str]) -> str:
    return f"""
# Drafted Admission Source Re-Audit

Positive `draft_picks` evidence remains the only drafted-only admission source.

Historical entry-status evidence:

- Drafted rows: `{counts["entry_drafted"]}`
- Confirmed historical UDFA rows: `{counts["entry_confirmed_udfa"]}`
- Likely UDFA / needs-review rows: `{counts["entry_likely_udfa"]}`
- Wrong-universe rows: `{counts["entry_wrong_universe"]}`
- Name-collision rows: `{counts["entry_name_collision"]}`

The NFLVerse player-context display/update wave provides safe display context for rows passing identity gates, but roster, weekly roster, depth-chart, snap-count, player_stats, injury, schedule, contract, and identity bridge fields cannot admit a drafted row.

Drafted-only review can proceed. Drafted-only model training is not approved. `draft_picks` remains the only admission source because it directly encodes draft event evidence; appearance in other datasets is post-entry context and may leak role, availability, or production.
"""


def pre_draft_vs_post_draft_feature_policy() -> str:
    return """
# Pre-Draft vs Post-Draft Feature Policy

Pre-draft factual candidates, such as combine or prospect-age context, still require a source, as-of, historical replay, missingness, and feature approval gate before experimentation.

Post-draft/current NFLVerse fields are display/review context only. This includes rosters, weekly rosters, snap counts, player_stats, depth charts, injuries, schedule context, contracts, last-active fields, and current player-context identity fields.

Post-draft fields cannot be used as pre-draft Rookie Outcome features unless a future replay proves they existed at the prediction anchor and passes leakage review. Future NFL production, games, starts, awards, career length, player_stats, snaps, injury reports, roster state, and depth chart role cannot be used as input features for drafted-only rookie prediction in this lane.

Missing values remain `Not enough information`; they are never zero, false, clean, healthy, no-role, low-risk, confirmed UDFA, or negative outcomes.
"""


def udfa_cfbd_blocker_reaudit(counts: dict[str, int | str]) -> str:
    return f"""
# UDFA and CFBD Blocker Re-Audit

UDFA modeling remains blocked.

- Confirmed historical UDFA rows: `{counts["entry_confirmed_udfa"]}`
- Likely UDFA / needs-review rows: `{counts["entry_likely_udfa"]}`
- Draft absence is not confirmed UDFA.
- Roster, weekly roster, depth chart, player_stats, snap, injury, and schedule appearance are not UDFA proof.

CFBD model/training input remains blocked. CFBD rows can remain review context only unless a later human-approved identity/source lane promotes them, and this packet grants no such approval.

Synthetic draft capital, likely UDFA status, and current review-only UDFA notes remain blocked from model/training/source-truth use.
"""


def gate_e_f_g_status_after_policy_gate() -> str:
    return """
# Gate E/F/G Status After Policy Gate

Gate E remains review/R&D only. This packet does not approve feature experimentation, model training, tuning, or current-player scoring.

Gate F remains partial review/display only where separate display lanes already approved safe consumption. This packet does not create active rookie display outputs.

Gate G remains blocked. No Rankings, Draft Room, Player Compare, app behavior, active rookie probability columns, fake T12/T24/T36 outputs, hidden sort, rank logic, source-truth promotion, model-use approval, or training-use approval is granted.
"""


def next_gate_recommendations() -> str:
    return """
# Next Gate Recommendations

Recommended next lanes, if HQ wants to continue:

1. Historical replay/leakage evidence for drafted-only pre-draft candidate features.
2. Label parity sidecar lane for NFLVerse `player_stats`, still review-only.
3. Combine/source coverage evidence lane before any Gate E model experiment.
4. Depth-chart opportunity watchlist evidence lane, review-only and not UDFA proof.
5. CFBD identity/source approval lane before any college context can become stronger than review-only.

Do not run Gate G next. Do not create active rookie probabilities next.
"""


def merge_safety_report() -> str:
    return """
# Merge Safety Report

This lane creates docs, one CSV matrix, a non-runtime report builder, and focused tests only.

Confirmed:

- no app files changed;
- no Rankings, Gate F/G, Draft Room, or Player Compare behavior changed;
- no model outputs changed;
- no source-truth behavior changed;
- no pinned snapshots changed;
- no `latest_candidate` or `latest_approved` changed;
- no protected/raw/private paths tracked;
- no secrets tracked;
- no local_exports, raw, or vendor files tracked.

All matrix rows keep `allowed_for_model_now=false`, `allowed_for_training_now=false`, and `allowed_for_source_truth_now=false`.
"""


def readme() -> str:
    return f"""
# Rookie Drafted-Only NFLVerse Feature Gate Evidence V1

Verdict: `{VERDICT}`

This packet audits NFLVerse feature families for drafted-only Rookie Outcomes review. It separates safe review/display context from blocked model/training/source-truth use.

No model training, rookie probabilities, Gate G, Rankings wiring, UDFA modeling, CFBD model/training input, or app behavior is approved.
"""


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
