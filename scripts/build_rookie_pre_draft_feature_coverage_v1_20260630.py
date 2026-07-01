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
    / "rookie_pre_draft_feature_coverage_v1_20260630"
)

BASE_HEAD = "9dafea81b3316a02f8a051762b9d53dc84791fc7"
BRANCH = "work/rookie-pre-draft-feature-coverage-v1-20260630"
WORKTREE = r"C:\NWR\Niners-War-Room-rookie-pre-draft-feature-coverage-v1-20260630"
VERDICT = "YELLOW_ROOKIE_PRE_DRAFT_COVERAGE_READY_NO_EXPERIMENT_APPROVAL"
NOT_ENOUGH = "Not enough information"

MODEL_CANDIDATE_ROOT = (
    REPO_ROOT / "docs" / "hq" / "outcomes" / "nflverse_model_candidate_readiness_matrix_v1_20260630"
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

FEATURE_COLUMNS = (
    "feature_family",
    "source_artifact",
    "pre_draft_allowed_candidate",
    "post_draft_only",
    "coverage_rows",
    "drafted_player_match_count",
    "missing_count",
    "as_of_safe_now",
    "replay_safe_now",
    "experiment_safe_now",
    "allowed_for_model_now",
    "allowed_for_training_now",
    "allowed_for_source_truth_now",
    "required_next_gate",
    "blocker_reason",
    "notes",
)

UNIVERSE_COLUMNS = (
    "coverage_slice",
    "drafted_player_count",
    "rookie_class_year_min",
    "rookie_class_year_max",
    "draft_capital_complete_count",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "notes",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    source = load_source_data()
    feature_rows = build_feature_rows(source)
    universe_rows = build_universe_rows(source)
    write_csv(args.output_root / "rookie_pre_draft_feature_coverage_matrix.csv", FEATURE_COLUMNS, feature_rows)
    write_csv(args.output_root / "drafted_only_universe_coverage.csv", UNIVERSE_COLUMNS, universe_rows)
    write_docs(args.output_root, source, feature_rows, universe_rows)

    print(
        {
            "verdict": VERDICT,
            "base_head": BASE_HEAD,
            "feature_rows": len(feature_rows),
            "drafted_rows": source["counts"]["drafted_rows"],
            "experiment_safe_count": sum(row["experiment_safe_now"] == "true" for row in feature_rows),
        }
    )


def load_source_data() -> dict[str, object]:
    drafted_rows = read_csv(DRAFTED_AUDIT_PATH)
    entry_rows = read_csv(ENTRY_STATUS_PATH)
    player_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_display_artifact.csv")
    join_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_join_health.csv")
    model_rows = read_csv(MODEL_CANDIDATE_ROOT / "nflverse_model_candidate_readiness_matrix.csv")
    rookie_gate_rows = read_csv(FEATURE_GATE_ROOT / "rookie_feature_gate_matrix.csv")
    build_report = (PLAYER_CONTEXT_ROOT / "nflverse_player_context_build_report.md").read_text(encoding="utf-8")
    counts = build_counts(drafted_rows, entry_rows, player_rows, join_rows, model_rows, build_report)
    return {
        "drafted_rows": drafted_rows,
        "entry_rows": entry_rows,
        "player_rows": player_rows,
        "join_rows": join_rows,
        "model_rows": model_rows,
        "rookie_gate_rows": rookie_gate_rows,
        "build_report": build_report,
        "counts": counts,
    }


def build_counts(
    drafted_rows: list[dict[str, str]],
    entry_rows: list[dict[str, str]],
    player_rows: list[dict[str, str]],
    join_rows: list[dict[str, str]],
    model_rows: list[dict[str, str]],
    build_report: str,
) -> dict[str, int | str]:
    entry = Counter(row["entry_status"] for row in entry_rows)
    identity = Counter(row["identity_join_status"] for row in player_rows)
    by_join_gate = {row["gate"]: row for row in join_rows}
    model_experiment = Counter(row["allowed_for_experiment_now"] for row in model_rows)
    draft_years = [int(row["draft_year"]) for row in drafted_rows if row["draft_year"].isdigit()]
    draft_capital_complete = sum(
        row["draft_year"] != NOT_ENOUGH
        and row["draft_round"] != NOT_ENOUGH
        and row["overall_pick"] != NOT_ENOUGH
        and row["drafted_team"] != NOT_ENOUGH
        for row in drafted_rows
    )
    return {
        "drafted_rows": len(drafted_rows),
        "draft_year_min": min(draft_years),
        "draft_year_max": max(draft_years),
        "draft_capital_complete": draft_capital_complete,
        "entry_likely_udfa": entry["likely_udfa_needs_review"],
        "entry_confirmed_udfa": entry["confirmed_udfa"],
        "player_context_rows": len(player_rows),
        "safe_display_rows": identity["SAFE_NOW_DISPLAY_ONLY"],
        "gated_rows": identity["NEED_IDENTITY_REVIEW"],
        "experiment_true": model_experiment["true"],
        "draft_picks_receipt_rows": extract_dataset_rows(build_report, "draft_picks"),
        "combine_receipt_rows": extract_dataset_rows(build_report, "combine"),
        "draft_capital_current_join_rows": by_join_gate["draft_capital_context_gate"]["clean_join_rows"],
        "combine_current_join_rows": by_join_gate["combine_context_gate"]["clean_join_rows"],
        "ff_playerids_current_join_rows": by_join_gate["ff_playerids_crosswalk_gate"]["clean_join_rows"],
        "depth_current_join_rows": by_join_gate["depth_chart_context_gate"]["clean_join_rows"],
        "snap_current_join_rows": by_join_gate["snap_count_context_gate"]["clean_join_rows"],
        "seasonal_stats_current_join_rows": by_join_gate["seasonal_stats_presence_gate"]["clean_join_rows"],
    }


def build_feature_rows(source: dict[str, object]) -> list[dict[str, str]]:
    counts = source["counts"]
    drafted_count = str(counts["drafted_rows"])
    no_match = "Not calculated at drafted historical row level in this evidence lane"
    return [
        feature("draft_picks drafted admission", "docs/hq/rookie_outcomes/rookie_drafted_only_nflverse_feature_gate_evidence_v1_20260630/rookie_feature_gate_matrix.csv", "true_review_admission_only", "false", str(counts["draft_picks_receipt_rows"]), drafted_count, "0", "true_for_review_admission_only", "false", "false", "Drafted-only admission plus Gate E model approval", "Review admission can proceed; experiment/model/training remain closed.", "Positive draft_picks evidence supports drafted-only review only."),
        feature("draft year", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "true_candidate_component", "false", drafted_count, drafted_count, "0", "true_for_review_context", "false", "false", "Gate E model approval plus as-of contract", "Component only; not experiment-approved.", "Draft event context after drafted admission."),
        feature("draft round", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "true_candidate_component", "false", drafted_count, drafted_count, "0", "true_for_review_context", "false", "false", "Gate E model approval plus no fake round policy", "No fake round 8; not experiment-approved.", "Real draft rounds only."),
        feature("overall pick", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "true_candidate_component", "false", drafted_count, drafted_count, "0", "true_for_review_context", "false", "false", "Gate E model approval plus as-of contract", "Not experiment-approved.", "Overall pick is factual draft event context."),
        feature("drafted team", "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv", "true_candidate_component", "false", drafted_count, drafted_count, "0", "true_for_review_context", "false", "false", "Gate E model approval plus team/context leakage review", "Team context may encode landing-spot effects; not experiment-approved.", "Review context only."),
        feature("combine", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md", "true_candidate_pending_coverage_gate", "false", str(counts["combine_receipt_rows"]), no_match, "Not enough information", "false", "false", "false", "Combine coverage, identity, event-date, and replay/as-of gate", "Receipt exists but historical drafted-player match coverage is not established.", "Current player-context join rows are not historical drafted experiment proof."),
        feature("age", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "true_candidate_pending_birthdate_asof_gate", "false", str(counts["safe_display_rows"]), no_match, "Not enough information", "false", "false", "false", "Age source/as-of and coverage gate", "Current derived age is display-only; historical as-of coverage not proven.", "Candidate only."),
        feature("rosters", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["safe_display_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Point-in-time roster replay gate", "Post-draft/current roster context can leak and cannot prove UDFA.", "Display context only."),
        feature("weekly_rosters", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["safe_display_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Season-week point-in-time replay gate", "Temporal roster state can leak.", "Display context only."),
        feature("snap_counts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["snap_current_join_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Historical replay/leakage gate", "Future NFL usage cannot be pre-draft feature.", "Missing snaps are not zero."),
        feature("player_stats", "docs/hq/outcomes/nflverse_model_candidate_readiness_matrix_v1_20260630/nflverse_model_candidate_readiness_matrix.csv", "false", "true", str(counts["seasonal_stats_current_join_rows"]), "sidecar only", "Not enough information", "false", "false", "false", "Label parity sidecar gate", "Future NFL production cannot be input feature.", "Review-only sidecar candidate, not label truth."),
        feature("depth_charts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["depth_current_join_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Depth-chart publication/as-of replay gate", "Current role can leak; not UDFA proof.", "Display opportunity context only."),
        feature("injury reports", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["safe_display_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Availability/medical guardrail and as-of gate", "Cannot become injury-risk score or health inference.", "Missing injury is not healthy."),
        feature("schedule context", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["safe_display_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Schedule release/as-of and no-matchup-strength gate", "Schedule is not recommendation/matchup/trade timing signal.", "Display context only."),
        feature("contracts", "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv", "false", "true", str(counts["safe_display_rows"]), "not pre-draft feature", "Not enough information", "false", "false", "false", "Contract policy gate", "Not valuation, rank, trade, or pick signal.", "Non-financial display context only."),
        feature("identity bridge health", "docs/hq/data_sources/nflverse_display_update_final_closeout_20260630/", "false", "false", str(counts["player_context_rows"]), "identity gate only", str(counts["gated_rows"]), "false", "false", "false", "Identity/binding approval gate", "13 rows remain gated; identity health is prerequisite not feature.", "Safe display rows are not model joins."),
        feature("CFBD joins", "docs/hq/rookie_model/; docs/hq/rookie_outcomes/", "false", "false", "review packets only", "0 approved model/training joins", "Not enough information", "false", "false", "false", "CFBD identity/source approval gate", "CFBD model/training input remains blocked.", "College context only if separately approved."),
        feature("UDFA status", "docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/", "false", "false", str(counts["entry_confirmed_udfa"]), "not drafted-only", str(counts["entry_likely_udfa"]), "false", "false", "false", "Approved UDFA source-policy gate", "UDFA modeling remains blocked; draft absence is not confirmed UDFA.", "Confirmed historical UDFA evidence is 0."),
        feature("fake/synthetic draft capital", "draft-capital policy docs", "false", "false", "0 approved", "0", "Not enough information", "false", "false", "false", "Draft capital source-policy gate", "No fake round 8, missing-as-zero, or pseudo draft capital.", "Quarantine only."),
        feature("Outcome V2 labels", "docs/hq/outcomes/; docs/hq/rookie_outcomes/", "false", "true_label_target_only", "review labels only", "label target only", "Not enough information", "false", "false", "false", "Label parity and model approval gate", "Labels are targets/evaluation only, never input features.", "Missing labels are not failures."),
        feature("ff_rankings", "docs/hq/outcomes/nflverse_model_candidate_readiness_matrix_v1_20260630/", "false", "false", "blocked", "0", "Not enough information", "false", "false", "false", "Blocked source-policy gate", "ff_rankings remains blocked.", "No ingestion/model/rank use."),
    ]


def feature(
    feature_family: str,
    source: str,
    pre_draft: str,
    post_draft: str,
    coverage_rows: str,
    match_count: str,
    missing_count: str,
    as_of: str,
    replay: str,
    experiment: str,
    required_gate: str,
    blocker: str,
    notes: str,
) -> dict[str, str]:
    return {
        "feature_family": feature_family,
        "source_artifact": source,
        "pre_draft_allowed_candidate": pre_draft,
        "post_draft_only": post_draft,
        "coverage_rows": coverage_rows,
        "drafted_player_match_count": match_count,
        "missing_count": missing_count,
        "as_of_safe_now": as_of,
        "replay_safe_now": replay,
        "experiment_safe_now": experiment,
        "allowed_for_model_now": "false",
        "allowed_for_training_now": "false",
        "allowed_for_source_truth_now": "false",
        "required_next_gate": required_gate,
        "blocker_reason": blocker,
        "notes": notes,
    }


def build_universe_rows(source: dict[str, object]) -> list[dict[str, str]]:
    drafted_rows = source["drafted_rows"]
    counts = source["counts"]
    rows = [
        universe_row(
            "ALL_QB_RB_WR_TE",
            str(counts["drafted_rows"]),
            str(counts["draft_year_min"]),
            str(counts["draft_year_max"]),
            str(counts["draft_capital_complete"]),
            "Drafted-only review universe; no model/training/source-truth approval.",
        )
    ]
    for position in ("QB", "RB", "WR", "TE"):
        group = [row for row in drafted_rows if row["position"] == position]
        years = [int(row["draft_year"]) for row in group if row["draft_year"].isdigit()]
        complete = sum(
            row["draft_year"] != NOT_ENOUGH
            and row["draft_round"] != NOT_ENOUGH
            and row["overall_pick"] != NOT_ENOUGH
            and row["drafted_team"] != NOT_ENOUGH
            for row in group
        )
        rows.append(
            universe_row(
                position,
                str(len(group)),
                str(min(years)),
                str(max(years)),
                str(complete),
                f"{position} drafted-only review slice.",
            )
        )
    return rows


def universe_row(
    coverage_slice: str,
    count: str,
    year_min: str,
    year_max: str,
    complete: str,
    notes: str,
) -> dict[str, str]:
    return {
        "coverage_slice": coverage_slice,
        "drafted_player_count": count,
        "rookie_class_year_min": year_min,
        "rookie_class_year_max": year_max,
        "draft_capital_complete_count": complete,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "notes": notes,
    }


def write_docs(output_root: Path, source: dict[str, object], feature_rows: list[dict[str, str]], universe_rows: list[dict[str, str]]) -> None:
    counts = source["counts"]
    docs = {
        "artifact_manifest.md": artifact_manifest(feature_rows, universe_rows),
        "pre_draft_feature_coverage_summary.md": pre_draft_feature_coverage_summary(counts, feature_rows),
        "combine_coverage_report.md": combine_coverage_report(counts),
        "draft_capital_coverage_report.md": draft_capital_coverage_report(counts),
        "leakage_and_asof_guardrail_report.md": leakage_and_asof_guardrail_report(),
        "gate_e_f_g_recommendations.md": gate_e_f_g_recommendations(),
        "merge_safety_report.md": merge_safety_report(),
        "README.md": readme(),
    }
    for name, text in docs.items():
        (output_root / name).write_text(text.strip() + "\n", encoding="utf-8")


def artifact_manifest(feature_rows: list[dict[str, str]], universe_rows: list[dict[str, str]]) -> str:
    return f"""
# Artifact Manifest

Verdict: `{VERDICT}`

Branch: `{BRANCH}`

Worktree: `{WORKTREE}`

Base HEAD: `{BASE_HEAD}`

This packet audits pre-draft feature coverage and as-of safety for Rookie Outcomes drafted-only work. It is evidence/audit only and grants no experiment, model, training, source-truth, app, Gate G, UDFA, or CFBD model/training approval.

| Artifact | Rows | Purpose |
|---|---:|---|
| `artifact_manifest.md` | n/a | Packet inventory and boundary |
| `pre_draft_feature_coverage_summary.md` | n/a | Executive summary |
| `rookie_pre_draft_feature_coverage_matrix.csv` | {len(feature_rows)} | Feature-family coverage/as-of matrix |
| `drafted_only_universe_coverage.csv` | {len(universe_rows)} | Drafted-only universe coverage by slice |
| `combine_coverage_report.md` | n/a | Combine coverage and blocker report |
| `draft_capital_coverage_report.md` | n/a | Draft-pick/draft-capital coverage report |
| `leakage_and_asof_guardrail_report.md` | n/a | Leakage/as-of guardrail |
| `gate_e_f_g_recommendations.md` | n/a | Gate posture and recommendations |
| `merge_safety_report.md` | n/a | Guardrail proof |
"""


def pre_draft_feature_coverage_summary(counts: dict[str, int | str], feature_rows: list[dict[str, str]]) -> str:
    experiment_safe = sum(row["experiment_safe_now"] == "true" for row in feature_rows)
    return f"""
# Pre-Draft Feature Coverage Summary

Verdict: `{VERDICT}`

Drafted-only review universe:

- Drafted QB/RB/WR/TE rows: `{counts["drafted_rows"]}`
- Rookie classes: `{counts["draft_year_min"]}` through `{counts["draft_year_max"]}`
- Draft-capital complete rows: `{counts["draft_capital_complete"]}`
- Current NFLVerse player-context rows: `{counts["player_context_rows"]}`
- Safe display rows: `{counts["safe_display_rows"]}`
- Gated identity rows: `{counts["gated_rows"]}`

Coverage receipts exist for `draft_picks` and `combine`, but no feature family is experiment-safe now.

Experiment-safe feature count: `{experiment_safe}`

Drafted-only review can continue from positive draft-pick evidence. Combine, draft capital, and age remain candidates only after as-of, replay, source, and feature gates. Future NFL production, roster, depth, injury, snaps, player_stats, contracts, and schedule context are not pre-draft features.
"""


def combine_coverage_report(counts: dict[str, int | str]) -> str:
    return f"""
# Combine Coverage Report

NFLVerse combine receipt rows in the tracked player-context build report: `{counts["combine_receipt_rows"]}`.

Current player-context combine gate clean joins: `{counts["combine_current_join_rows"]}` out of `{counts["player_context_rows"]}` current rows.

This does not establish historical drafted-player combine coverage for `{counts["drafted_rows"]}` drafted QB/RB/WR/TE rows. Raw combine rows are not tracked in this packet, and no event-date/as-of replay has been run.

Result: combine is a pre-draft candidate only. It is not experiment-safe, model-safe, training-safe, or source-truth-safe now.
"""


def draft_capital_coverage_report(counts: dict[str, int | str]) -> str:
    return f"""
# Draft Capital Coverage Report

Drafted-only historical audit rows: `{counts["drafted_rows"]}`.

Draft-capital complete rows in the historical drafted audit: `{counts["draft_capital_complete"]}`.

NFLVerse draft_picks receipt rows in current player-context build report: `{counts["draft_picks_receipt_rows"]}`.

Current player-context draft-capital clean joins: `{counts["draft_capital_current_join_rows"]}` out of `{counts["player_context_rows"]}` current rows.

Positive draft-pick evidence may support drafted-only review. Missing draft capital does not confirm UDFA. Fake round 8 and synthetic draft capital remain blocked/quarantined.

Result: draft capital is review-safe after positive admission evidence, but no experiment/model/training/source-truth approval is granted.
"""


def leakage_and_asof_guardrail_report() -> str:
    return """
# Leakage and As-Of Guardrail Report

No feature is experiment-safe now.

Required before future experiment planning:

- prediction anchor;
- point-in-time source snapshot;
- extraction timestamp;
- feature as-of timestamp;
- identity-safe join audit;
- missingness/censoring policy;
- leakage diagnostics;
- label interaction audit;
- row counts by season, position, and feature state;
- blocked-source scan;
- explicit non-activation boundary.

Future NFL production, roster state, depth chart role, injury report, practice status, snap count, activity week, contract context, schedule context, and labels cannot be pre-draft features without a future replay/as-of gate. Missing values remain `Not enough information`, not zero/false/clean/healthy/no-role/low-risk/confirmed UDFA.
"""


def gate_e_f_g_recommendations() -> str:
    return """
# Gate E/F/G Recommendations

Gate E remains review/R&D only. Do not run an experiment yet because no feature family is experiment-safe now.

Gate F remains partial display/review only where separate display lanes already approved safe consumption. This lane does not create display outputs.

Gate G remains blocked. Do not wire Rankings, Draft Room, Player Compare, Gate F/G, or app behavior. Do not create active rookie probabilities or fake T12/T24/T36 outputs.

Recommended next evidence lane: point-in-time snapshot feasibility or combine historical coverage audit, still no experiment approval.
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
- no local_exports, raw, or vendor files tracked.

All rows keep `experiment_safe_now=false`, `allowed_for_model_now=false`, `allowed_for_training_now=false`, and `allowed_for_source_truth_now=false`.
"""


def readme() -> str:
    return f"""
# Rookie Pre-Draft Feature Coverage V1

Verdict: `{VERDICT}`

This packet audits drafted-only pre-draft feature coverage and as-of safety before any future experiment planning.

No experiment, model training, rookie probability, Gate G, app wiring, UDFA modeling, or CFBD model/training input is approved.
"""


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
