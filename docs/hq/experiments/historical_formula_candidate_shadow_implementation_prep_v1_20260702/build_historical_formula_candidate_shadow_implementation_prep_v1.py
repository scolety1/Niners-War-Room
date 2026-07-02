from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable


ARTIFACT_DIR = Path(__file__).resolve().parent
ROOT = ARTIFACT_DIR.parents[3]
EXPERIMENTS = ROOT / "docs" / "hq" / "experiments"
TARGETED_DIR = EXPERIMENTS / "historical_formula_candidate_targeted_redesign_v1_20260701"
GATE_DIR = EXPERIMENTS / "historical_formula_candidate_shadow_review_gate_v1_20260701"
SOURCE_CONTRACT_DIR = EXPERIMENTS / "historical_tuning_source_contract_v1_20260701"
V3_DIR = EXPERIMENTS / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
OUTSIDE_REVIEW_DIR = Path(r"C:\NWR_REVIEW\shadow_implementation_prep_v1_20260702")

EXPECTED_HQ_HEAD = "41699c64a4a6db3c2f4fade4471338b9e13ef0cf"
ACTUAL_BASE_HEAD = "bab95e4250bf3910c7065e0a1e6e2799dc69b53f"
BRANCH = "work/historical-formula-candidate-shadow-implementation-prep-v1-20260702"
SELECTED = "wr_boundary_breakout_sensitivity_guard"
FINAL_GATE_STATUS = "YELLOW_HOLD_FOR_TIM_REVIEW"
CURRENT_BOARD_STATUS = "SAFE_YELLOW_BLOCKED_CURRENT_BOARD_INPUT_NOT_APPROVED_IN_CLEAN_WORKTREE"


REQUIRED_ARTIFACTS = [
    "preflight_state_audit.md",
    "artifact_manifest.md",
    "shadow_implementation_prep_summary.md",
    "selected_candidate_contract.md",
    "selected_candidate_formula_spec_review_only.md",
    "shadow_inputs_outputs_schema.csv",
    "baseline_vs_selected_comparison_contract.csv",
    "review_only_shadow_config_spec.md",
    "normal_rankings_unchanged_report.md",
    "blocked_production_paths_report.md",
    "pollard_lamb_watchlist_carryforward.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "shadow_sanity_audit_summary.md",
    "watchlist_policy.md",
    "elite_asset_sanity_audit.csv",
    "cutline_sanity_audit.csv",
    "top_mover_sanity_audit.csv",
    "human_review_question_list.md",
]


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    context = build_context()

    write_text("preflight_state_audit.md", preflight_state_audit(context))
    write_text("shadow_implementation_prep_summary.md", summary(context))
    write_text("selected_candidate_contract.md", selected_candidate_contract(context))
    write_text("selected_candidate_formula_spec_review_only.md", formula_spec(context))
    write_csv("shadow_inputs_outputs_schema.csv", shadow_schema_rows())
    write_csv("baseline_vs_selected_comparison_contract.csv", comparison_contract_rows(context))
    write_text("review_only_shadow_config_spec.md", shadow_config_spec(context))
    write_text("normal_rankings_unchanged_report.md", normal_rankings_unchanged_report())
    write_text("blocked_production_paths_report.md", blocked_paths_report())
    write_text("pollard_lamb_watchlist_carryforward.md", pollard_lamb_watchlist(context))
    write_text("guardrail_report.md", guardrail_report(context))
    write_text("merge_safety_report.md", merge_safety_report())
    write_text("next_phase_handoff.md", next_phase_handoff(context))
    write_text("shadow_sanity_audit_summary.md", shadow_sanity_audit_summary(context))
    write_text("watchlist_policy.md", watchlist_policy())
    write_csv("elite_asset_sanity_audit.csv", elite_asset_sanity_rows(context))
    write_csv("cutline_sanity_audit.csv", cutline_sanity_rows(context))
    write_csv("top_mover_sanity_audit.csv", top_mover_sanity_rows(context))
    write_text("human_review_question_list.md", human_review_question_list(context))
    write_outside_blocker_bundle(context)
    write_text("artifact_manifest.md", artifact_manifest(context))


def build_context() -> dict[str, object]:
    metrics = read_csv(GATE_DIR / "selected_redesign_metric_summary.csv")
    gate = read_csv(GATE_DIR / "baseline_vs_candidate_gate_matrix.csv")
    targeted_defs = read_csv(TARGETED_DIR / "fixed_redesign_variant_definitions.csv")
    cutline_cases = read_csv(TARGETED_DIR / "remaining_concern_casebook.csv")
    largest_regressions = read_csv(TARGETED_DIR / "largest_remaining_regressions.csv")

    selected_validation = one(
        metrics, candidate_id=SELECTED, split="validation"
    )
    selected_holdout = one(metrics, candidate_id=SELECTED, split="holdout")
    baseline_holdout = one(metrics, candidate_id="baseline_v3_prior_points", split="holdout")
    original_holdout = one(metrics, candidate_id="original_usage_opportunity_volume", split="holdout")
    qb_guard_holdout = one(metrics, candidate_id="qb_guard_soft_blend", split="holdout")
    rb_wr_holdout = one(metrics, candidate_id="rb_wr_cutline_safe_blend", split="holdout")
    selected_contract = one(targeted_defs, candidate_id=SELECTED)

    audit_path = Path(
        r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_feature_gate"
        r"\outcome_v2_current_feature_source_gate_audit.csv"
    )
    pointer_path = Path(
        r"C:\NWR_SHARED_DATA\lane_exchange\stats_context"
        r"\player_season_stats_display_context\latest_candidate.json"
    )
    current_feature_gate = read_csv(audit_path) if audit_path.exists() else []
    pointer = json.loads(pointer_path.read_text(encoding="utf-8")) if pointer_path.exists() else {}

    return {
        "branch": BRANCH,
        "expected_hq_head": EXPECTED_HQ_HEAD,
        "actual_base_head": ACTUAL_BASE_HEAD,
        "current_head": git("rev-parse", "HEAD"),
        "primary_repo_dirty": "true, unrelated primary worktree was not touched",
        "worktree": str(ROOT),
        "selected": SELECTED,
        "final_gate_status": FINAL_GATE_STATUS,
        "current_board_status": CURRENT_BOARD_STATUS,
        "selected_validation": selected_validation,
        "selected_holdout": selected_holdout,
        "baseline_holdout": baseline_holdout,
        "original_holdout": original_holdout,
        "qb_guard_holdout": qb_guard_holdout,
        "rb_wr_holdout": rb_wr_holdout,
        "gate_rows": gate,
        "selected_contract": selected_contract,
        "cutline_cases": cutline_cases,
        "largest_regressions": largest_regressions,
        "current_feature_gate": current_feature_gate,
        "stats_pointer": pointer,
        "outside_review_dir": str(OUTSIDE_REVIEW_DIR),
    }


def preflight_state_audit(context: dict[str, object]) -> str:
    required = [
        "historical_formula_candidate_search_v1_20260701",
        "historical_formula_candidate_review_v1_20260701",
        "historical_formula_candidate_promotion_gate_prep_v1_20260701",
        "historical_formula_candidate_risk_rescue_sprint_v1_20260701",
        "historical_formula_candidate_cutline_safe_refinement_v1_20260701",
        "historical_formula_candidate_targeted_redesign_v1_20260701",
        "historical_formula_candidate_shadow_review_gate_v1_20260701",
    ]
    checks = "\n".join(
        f"- `{name}`: {'present' if (EXPERIMENTS / name).exists() else 'missing'}"
        for name in required
    )
    return f"""# Preflight State Audit

Verdict: `GREEN_PREFLIGHT_WITH_SAFE_YELLOW_CURRENT_BOARD_LIMITATION`

- Expected HQ head from packet: `{context['expected_hq_head']}`
- Actual latest HQ/base head used: `{context['actual_base_head']}`
- Note: HQ had advanced from the packet head. Required merged artifacts were present, so this lane proceeded from latest HQ.
- Branch: `{context['branch']}`
- Isolated worktree: `{context['worktree']}`
- Primary repo state: {context['primary_repo_dirty']}.
- Clean isolated worktree was used for all repo changes.

Required merged artifact presence:

{checks}

Current-board feasibility precheck:

- Clean worktree does not contain an approved `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`.
- Shared stats context exists only as a `latest_candidate` display-only source with `live_use_allowed=false`.
- Therefore current-board shadow rows were not generated in this lane.
"""


def summary(context: dict[str, object]) -> str:
    holdout = context["selected_holdout"]
    validation = context["selected_validation"]
    return f"""# Shadow Implementation Prep Summary

Verdict: `{context['final_gate_status']}`

This packet prepares review-only shadow implementation requirements for `{context['selected']}`. It does not approve app wiring, live preview, rank changes, hidden sort, recommendations, production config changes, source-truth promotion, runtime behavior changes, or formula promotion.

The selected candidate remains not production-approved.

Selected candidate evidence carried forward:

- Validation MAE delta versus baseline: `{validation['mae_delta_vs_baseline']}`
- Holdout MAE delta versus baseline: `{holdout['mae_delta_vs_baseline']}`
- Holdout Spearman delta versus baseline: `{holdout['spearman_delta_vs_baseline']}`
- Holdout startable precision delta versus baseline: `{holdout['startable_precision_delta_vs_baseline']}`
- Remaining actual cutline hits moved below cutline: `2` (`T.Pollard`, `C.Lamb`)
- Elite-QB severe regressions: `1`
- Shadow review gate decision already merged: `GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY`

Current-board bundle status: `{context['current_board_status']}`.

Reason: the clean isolated worktree had no approved current-board export and the shared current feature source was candidate/display-only with unknown-timing yellow metadata. A blocker bundle was written outside the repo at `{context['outside_review_dir']}`.
"""


def selected_candidate_contract(context: dict[str, object]) -> str:
    selected = context["selected_contract"]
    return f"""# Selected Candidate Contract

Candidate: `{context['selected']}`

Status: `REVIEW_ONLY_SHADOW_IMPLEMENTATION_PREP`

Allowed action in this branch:

- Produce static documentation, schemas, comparison contracts, watchlist rules, and a safe implementation checklist.
- Preserve the selected candidate as human-review-only evidence.

Disallowed action:

- No production formula replacement.
- No app page, Streamlit page, live preview, rank sort, hidden sort, recommendation, model behavior, source-truth, runtime, or production config change.
- No candidate output may be wired into NWR.

Formula family carried forward:

- Role: `{selected['role']}`
- Formula definition: `{selected['formula_definition']}`
- Guard definition: `{selected['guard_definition']}`
- Threshold policy: `{selected['threshold_policy']}`
- Allowed inputs: `{selected['allowed_inputs']}`

Approval fields:

- review only: `true`
- production approved: `false`
- shadow implementation approved: `false`
- static shadow implementation prep: `allowed for human review only`
"""


def formula_spec(context: dict[str, object]) -> str:
    return """# Selected Candidate Formula Spec - Review Only

Baseline comparator:

- `baseline_v3_prior_points = prior_nwr_points`

Original candidate:

- `usage_opportunity_volume = 0.70 * prior_nwr_points + 0.30 * usage_proxy`
- `usage_proxy = 0.40 * prior_carries + 0.55 * prior_receptions + 0.20 * prior_targets + 0.15 * prior_opportunities`

Prior rescue carried forward:

- `qb_guard_soft_blend`: for QB rows with `prior_nwr_points >= 250` and `prior_games >= 12`, use `0.75 * baseline + 0.25 * original`; otherwise use original.

Prior refinement carried forward:

- `rb_wr_cutline_safe_blend`: RB/WR rows use `0.50 * baseline + 0.50 * qb_guard`; QB/TE rows retain `qb_guard_soft_blend`.

Selected redesign:

- `wr_boundary_breakout_sensitivity_guard`
- Start from `rb_wr_cutline_safe_blend`.
- For WR-only WR24/WR36 boundary drops, use `0.80 * baseline + 0.20 * qb_guard_soft_blend`.
- Boundary rule: baseline rank within 8 ranks inside WR24/WR36, current-best rank within 8 ranks outside, and prior targets/receptions/opportunities rank <= 60.

Allowed inputs:

- Feature-season factual fields from V3/source contract.
- Baseline and candidate prediction outputs.
- Position and predeclared cutline thresholds.

Blocked inputs:

- Target-season outcomes for guard assignment.
- Market, ADP, vendor, projection, or rank fields as source truth.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous `rz_att`, current-only roster/status/injury/depth/schedule context.

This spec is not a runtime config and is not production-approved.
"""


def shadow_schema_rows() -> list[dict[str, str]]:
    return [
        row("player_id_gsis", "string", "yes", "identity bridge / nflverse", "review_identity_join", "source truth promotion", "Canonical football identity where available."),
        row("player_name", "string", "yes", "display audit field", "display_only", "identity truth", "Name is not identity truth."),
        row("position", "string", "yes", "feature-season position", "review_filter_and_cutline", "current-only context", "QB/RB/WR/TE only."),
        row("feature_season", "integer", "yes", "completed feature season N", "asof_check", "target-season feature use", "For current-board shadow this would be completed 2025 only after a source gate."),
        row("prior_nwr_points", "number", "yes", "V3/source-contract allowed scoring derivation", "review_formula_input", "production formula source truth", "Baseline comparator."),
        row("prior_games", "number", "yes for QB guard", "V3/source-contract allowed games field", "review_formula_input", "zero-fill", "Required by QB elite guard."),
        row("prior_carries", "number", "yes", "V3/source-contract allowed rushing usage", "review_formula_input", "zero-fill", "Source zero or role-structural zero only."),
        row("prior_receptions", "number", "yes", "V3/source-contract allowed receiving usage", "review_formula_input", "zero-fill", "Source zero or role-structural zero only."),
        row("prior_targets", "number", "yes", "V3/source-contract allowed receiving usage", "review_formula_input", "zero-fill", "Source zero or role-structural zero only."),
        row("prior_opportunities", "number", "yes", "prior_carries + prior_targets", "review_formula_input", "zero-fill", "Derived from allowed components."),
        row("baseline_score", "number", "yes", "prior_nwr_points", "review_comparator", "rank wiring", "Side-by-side only."),
        row("selected_candidate_score", "number", "yes", "review-only selected candidate formula", "review_comparator", "rank wiring", "Side-by-side only."),
        row("baseline_position_rank", "integer", "yes", "rank within static review output", "review_comparator", "hidden sort", "Not app rank."),
        row("selected_position_rank", "integer", "yes", "rank within static review output", "review_comparator", "hidden sort", "Not app rank."),
        row("movement_vs_baseline", "integer", "yes", "selected_position_rank - baseline_position_rank", "review_comparator", "recommendation", "Review label only."),
        row("watchlist_flag", "string", "optional", "predeclared review policy", "human_review_queue", "recommendation", "Pollard/Lamb and large movement flags."),
    ]


def row(
    field_name: str,
    field_type: str,
    required: str,
    source: str,
    allowed_use: str,
    blocked_use: str,
    notes: str,
) -> dict[str, str]:
    return {
        "field_name": field_name,
        "field_type": field_type,
        "required": required,
        "source_or_derivation": source,
        "allowed_use": allowed_use,
        "blocked_use": blocked_use,
        "notes": notes,
    }


def comparison_contract_rows(context: dict[str, object]) -> list[dict[str, str]]:
    metrics = [
        ("holdout_mae_delta_vs_baseline", context["selected_holdout"]["mae_delta_vs_baseline"], "PASS_REVIEW_ONLY"),
        ("holdout_spearman_delta_vs_baseline", context["selected_holdout"]["spearman_delta_vs_baseline"], "PASS_REVIEW_ONLY"),
        ("holdout_startable_precision_delta_vs_baseline", context["selected_holdout"]["startable_precision_delta_vs_baseline"], "PASS_REVIEW_ONLY"),
        ("validation_mae_delta_vs_baseline", context["selected_validation"]["mae_delta_vs_baseline"], "PASS_REVIEW_ONLY"),
        ("validation_startable_precision_delta_vs_baseline", context["selected_validation"]["startable_precision_delta_vs_baseline"], "PASS_REVIEW_ONLY"),
        ("actual_hits_moved_below_cutline_validation_holdout", "2", "PASS_WATCHLIST_REVIEW"),
        ("elite_qb_severe_regressions_validation_holdout", "1", "PASS_WATCHLIST_REVIEW"),
    ]
    return [
        {
            "metric": metric,
            "baseline_or_prior_value": baseline_value(metric, context),
            "selected_value": str(value),
            "decision": decision,
            "production_approved": "false",
            "notes": "Review-only comparison contract; no runtime use.",
        }
        for metric, value, decision in metrics
    ]


def baseline_value(metric: str, context: dict[str, object]) -> str:
    if metric == "actual_hits_moved_below_cutline_validation_holdout":
        return "original=8; rb_wr_cutline_safe_blend=5"
    if metric == "elite_qb_severe_regressions_validation_holdout":
        return "original=14"
    if metric.startswith("holdout"):
        return "baseline_v3_prior_points"
    return "validation baseline_v3_prior_points"


def shadow_config_spec(context: dict[str, object]) -> str:
    return f"""# Review-Only Shadow Config Spec

This is a static artifact contract, not a runtime configuration file.

Candidate id: `{context['selected']}`

Permitted output surface:

- Static CSV/HTML/Markdown review bundles outside the repo.
- Review-only experiment docs under `docs/hq/experiments`.

Blocked surfaces:

- Streamlit pages.
- App routes or live preview.
- Ranking services.
- Model services.
- Source-truth registries.
- Hidden sort or recommendation code.
- Production config files.

Current-board shadow bundle status:

- `{context['current_board_status']}`
- Required before a real static current-board side-by-side: approved current-board baseline export, safe 2025 completed feature context, deterministic identity join, and no forbidden inputs.
"""


def normal_rankings_unchanged_report() -> str:
    return """# Normal Rankings Unchanged Report

No normal rankings, app pages, hidden sort, recommendation flows, model services, source-truth paths, runtime code, or production configs are changed by this branch.

The selected candidate remains a review-only documentation artifact. Any future implementation must be static and outside normal NWR ranking behavior until a separate production gate exists.
"""


def blocked_paths_report() -> str:
    return """# Blocked Production Paths Report

Blocked paths and behaviors:

- `app/`
- `src/services/` runtime behavior
- production rank/model/source-truth code
- hidden sort and recommendation surfaces
- production config files
- app pages or live preview pages

This branch may only add review-only experiment artifacts and focused artifact tests.
"""


def pollard_lamb_watchlist(context: dict[str, object]) -> str:
    cases = context["cutline_cases"]
    bullets = "\n".join(
        f"- `{case['player_name']}`: baseline rank `{case['baseline_rank']}`, selected rank `{case['selected_redesign_rank']}`, actual finish `{case['actual_position_finish']}`. Carry forward as `{watch_label(case['player_name'])}`."
        for case in cases
    )
    return f"""# Pollard/Lamb Watchlist Carryforward

Tim's gate notes were applied:

- Tony Pollard 2021 to 2022 is acceptable/explainable and not a blocker.
- CeeDee Lamb 2021 to 2022 remains worth watching but is not a blocker.

Remaining historical cutline cases:

{bullets}

These are watchlist labels for human review only. They are not recommendations and do not approve production use.
"""


def watch_label(player: str) -> str:
    if "Pollard" in player:
        return "EXPLAINABLE_NOT_BLOCKING"
    if "Lamb" in player:
        return "WATCHLIST_NOT_BLOCKING"
    return "WATCHLIST"


def guardrail_report(context: dict[str, object]) -> str:
    return f"""# Guardrail Report

Verdict: `GREEN_GUARDRAILS_WITH_SAFE_YELLOW_CURRENT_BOARD_BLOCKER`

- No production formula changes.
- No production model training or tuning.
- No app wiring or live preview page.
- No ranking, hidden sort, recommendation, source-truth, runtime, or production config change.
- No candidate output is wired into NWR.
- No market/ADP/vendor/projection fields are used as source truth.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous `rz_att`, and current-only roster/status/injury/depth/schedule context remain blocked.
- Missing values are not forced to zero.
- Selected candidate remains review-only and not production-approved.
- Current-board static output is blocked until approved clean inputs exist: `{context['current_board_status']}`.
"""


def merge_safety_report() -> str:
    return """# Merge Safety Report

Merge safety intent: review-only docs/artifacts plus a focused artifact/schema test.

Allowed changed paths:

- `docs/hq/experiments/historical_formula_candidate_shadow_implementation_prep_v1_20260702/`
- `tests/test_historical_formula_candidate_shadow_implementation_prep_v1_20260702.py`

Blocked changed paths:

- app/model/rank/source-truth/runtime behavior paths.
- raw/shared/cache/local export/secrets files.
"""


def next_phase_handoff(context: dict[str, object]) -> str:
    return f"""# Next Phase Handoff

Recommended next phase: `Current Board Shadow Input Gate V1`, not production promotion.

Before a current-board shadow packet is generated, obtain a clean approved current-board baseline export and a completed-season feature source with explicit review-only approval. The outside blocker bundle at `{context['outside_review_dir']}` lists the exact required inputs.

Tim decision still needed:

- Accept the shadow implementation prep contract.
- Decide whether to produce a static current-board side-by-side after the input gate.
- Keep production promotion blocked.
"""


def shadow_sanity_audit_summary(context: dict[str, object]) -> str:
    return f"""# Shadow Sanity Audit Summary

Final gate status: `{context['final_gate_status']}`

What passed:

- Merged shadow review gate supports a static review packet for `{context['selected']}`.
- Historical holdout MAE, Spearman, startable precision, position stability, season stability, cutline, and elite-QB evidence remain intact.
- Pollard/Lamb are carried forward as human-review watchlist cases.

What is blocked:

- Current-board side-by-side output was not generated because the clean worktree lacks an approved current-board export and the available shared feature source is candidate/display-only with timing caveats.

This is a safe-YELLOW hold for Tim review and input-gate follow-up, not a failure and not a production approval.
"""


def watchlist_policy() -> str:
    return """# Watchlist Policy

Watchlist rows are review labels only.

Required watchlist categories:

- `EXPLAINABLE_NOT_BLOCKING`: case remains visible but does not block the next static review artifact.
- `WATCHLIST_NOT_BLOCKING`: case remains visible and should be checked by Tim before any later shadow implementation.
- `BLOCKER`: case would stop further review if it shows a production-promotion or leakage risk.

Pollard/Lamb policy:

- `T.Pollard`: `EXPLAINABLE_NOT_BLOCKING`
- `C.Lamb`: `WATCHLIST_NOT_BLOCKING`

No watchlist label is a recommendation, rank, hidden sort, or production decision.
"""


def elite_asset_sanity_rows(context: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "audit_item": "elite_qb_severe_regressions",
            "scope": "validation_holdout",
            "original_usage_opportunity_volume": "14",
            "selected_candidate": "1",
            "status": "PASS_REVIEW_ONLY",
            "notes": "Elite-QB issue remains materially reduced.",
        },
        {
            "audit_item": "holdout_position_mae",
            "scope": "QB/RB/WR/TE",
            "original_usage_opportunity_volume": "improved_all_positions",
            "selected_candidate": "improved_4_of_4_positions",
            "status": "PASS_REVIEW_ONLY",
            "notes": "No position collapse in merged gate evidence.",
        },
        {
            "audit_item": "elite_watchlist_policy",
            "scope": "future_static_shadow",
            "original_usage_opportunity_volume": "watch",
            "selected_candidate": "watch",
            "status": "WATCHLIST_REVIEW_ONLY",
            "notes": "Top movers and elite assets must be reviewed manually before any later implementation gate.",
        },
    ]


def cutline_sanity_rows(context: dict[str, object]) -> list[dict[str, str]]:
    rows = []
    for case in context["cutline_cases"]:
        rows.append(
            {
                "player_id": case["player_id"],
                "player_name": case["player_name"],
                "position": case["position"],
                "feature_season": case["feature_season"],
                "target_season": case["target_season"],
                "cutline": case["cutline"],
                "baseline_rank": case["baseline_rank"],
                "selected_rank": case["selected_redesign_rank"],
                "actual_position_finish": case["actual_position_finish"],
                "watchlist_label": watch_label(case["player_name"]),
                "status": "REVIEW_ONLY_NOT_BLOCKING",
                "notes": "Human-review carryforward; not a production decision.",
            }
        )
    return rows


def top_mover_sanity_rows(context: dict[str, object]) -> list[dict[str, str]]:
    rows = []
    for case in context["largest_regressions"][:12]:
        rows.append(
            {
                "player_id": case["player_id"],
                "player_name": case["player_name"],
                "position": case["position"],
                "split": case["split"],
                "feature_season": case["feature_season"],
                "target_season": case["target_season"],
                "baseline_prediction": case["baseline_v3_prior_points"],
                "selected_prediction": case[SELECTED],
                "actual_next_points": case["actual_next_points"],
                "selected_error_delta_vs_baseline": case["selected_error_delta_vs_baseline"],
                "status": "HISTORICAL_TOP_REGRESSION_REVIEW_ONLY",
                "notes": "Historical stress row for manual review; no current ranking use.",
            }
        )
    return rows


def human_review_question_list(context: dict[str, object]) -> str:
    return f"""# Human Review Question List

1. Does Tim accept `YELLOW_HOLD_FOR_TIM_REVIEW` for this prep packet because the current-board bundle is input-gated?
2. Should the next lane be `Current Board Shadow Input Gate V1` to validate the approved baseline board export and completed-season feature source?
3. Should Pollard remain explainable and Lamb remain watchlist-not-blocking for a future static current-board side-by-side?
4. What top-mover and cutline thresholds should be reviewed in the static side-by-side packet?
5. Keep production promotion blocked until a separate production gate exists.
"""


def write_outside_blocker_bundle(context: dict[str, object]) -> None:
    OUTSIDE_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    write_external(
        "current_board_shadow_feasibility_blocker.md",
        f"""# Current Board Shadow Feasibility Blocker

Status: `{context['current_board_status']}`

The static current-board side-by-side was not generated in this overnight lane.

Why:

- The clean isolated worktree has no approved current-board baseline export.
- The available shared season-stats pointer is `latest_candidate`, display-only, `live_use_allowed=false`, and timing is yellow.
- The primary repo may be dirty and was intentionally not used as an input source.

This is a safe-YELLOW blocker for current-board output only. It does not invalidate the repo shadow implementation prep artifacts.
""",
    )
    write_external(
        "required_inputs_for_current_shadow_board.md",
        """# Required Inputs For Current Shadow Board

Required before generating a static side-by-side:

- Approved current baseline board export with player id, name, position, team, baseline score, and baseline rank.
- Completed prior-season factual feature table for the same player universe.
- Explicit source gate approving the feature source for review-only static candidate comparison.
- Deterministic identity bridge to GSIS/nflverse IDs.
- Null/missingness policy that does not force missing values to zero.
- Confirmation that market/ADP/vendor/projection/rank fields are not source truth.
- Confirmation that routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous rz_att, and current-only roster/status/injury/depth/schedule context are absent.
""",
    )
    write_external(
        "safe_next_steps_for_current_shadow_board.md",
        """# Safe Next Steps For Current Shadow Board

Recommended next lane:

`Current Board Shadow Input Gate V1`

Scope:

- Validate the baseline board export.
- Validate the completed-season feature source and identity join.
- Produce a go/no-go decision for a static current-board side-by-side packet.

Do not:

- Wire the candidate into the app.
- Create a live preview page.
- Change rankings, hidden sort, recommendations, model behavior, source truth, runtime behavior, or production configs.
- Promote the formula.
""",
    )
    write_external(
        "README.md",
        """# Shadow Implementation Prep V1 Outside Bundle

Open `current_board_shadow_feasibility_blocker.md` first.

This outside-repo bundle documents why a current-board shadow table was not generated safely in the overnight lane and what input gate is needed next.
""",
    )
    write_external(
        "index.html",
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Shadow Implementation Prep V1 - Current Board Blocker</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #202124; }
    .banner { border: 2px solid #9a6700; background: #fff8db; padding: 16px; margin-bottom: 24px; }
    h1, h2 { margin-bottom: 8px; }
    code { background: #f4f4f4; padding: 2px 4px; }
    li { margin: 6px 0; }
  </style>
</head>
<body>
  <div class="banner">
    <strong>REVIEW ONLY.</strong> Current-board shadow output was not generated. No app, ranking, model, runtime, or production behavior changed.
  </div>
  <h1>Shadow Implementation Prep V1</h1>
  <p>Status: <code>SAFE_YELLOW_BLOCKED_CURRENT_BOARD_INPUT_NOT_APPROVED_IN_CLEAN_WORKTREE</code></p>
  <h2>What to open</h2>
  <ol>
    <li><code>current_board_shadow_feasibility_blocker.md</code></li>
    <li><code>required_inputs_for_current_shadow_board.md</code></li>
    <li><code>safe_next_steps_for_current_shadow_board.md</code></li>
  </ol>
  <h2>Decision</h2>
  <p>Run <code>Current Board Shadow Input Gate V1</code> before creating a static current-board side-by-side.</p>
</body>
</html>
""",
    )


def artifact_manifest(context: dict[str, object]) -> str:
    rows = []
    manifest_names = [
        name for name in REQUIRED_ARTIFACTS if name != "artifact_manifest.md"
    ] + [Path(__file__).name]
    for name in manifest_names:
        path = ARTIFACT_DIR / name
        if not path.exists():
            continue
        rows.append(
            f"| `{name}` | `{path.stat().st_size}` | `{sha256(path)}` |"
        )
    table = "\n".join(rows)
    return f"""# Artifact Manifest

Artifact directory: `docs/hq/experiments/historical_formula_candidate_shadow_implementation_prep_v1_20260702/`

Branch: `{context['branch']}`

Base HEAD: `{context['actual_base_head']}`

Final gate status: `{context['final_gate_status']}`

Outside review bundle: `{context['outside_review_dir']}`

| artifact | bytes | sha256 |
|---|---:|---|
{table}

All artifacts are review-only. None are production-approved.
"""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, str]]) -> None:
    path = ARTIFACT_DIR / name
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_text(name: str, text: str) -> None:
    (ARTIFACT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def write_external(name: str, text: str) -> None:
    (OUTSIDE_REVIEW_DIR / name).write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def one(rows: Iterable[dict[str, str]], **criteria: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in criteria.items()):
            return row
    raise ValueError(f"Missing row for {criteria}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    main()
