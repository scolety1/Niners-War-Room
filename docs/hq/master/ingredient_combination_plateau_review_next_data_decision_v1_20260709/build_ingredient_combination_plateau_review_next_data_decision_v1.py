from __future__ import annotations

import csv
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_ROOKIE_COMMIT = "f8978155f40b2cb9ba36b7b15947953cb6ae7542"
VERDICT = "GREEN_NEXT_DATA_LANE_SELECTED_AFTER_PLATEAU_REVIEW"
NEXT_LANE = "Team Offensive Environment Sidecar V1"


def write_csv(name: str, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path = OUT_DIR / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8")


ingredient_status_rows = [
    {
        "ingredient": "PFR RB broken tackles",
        "status": "FAILED_NO_INCREMENTAL_SIGNAL",
        "best_result": "raw broken tackles Spearman 0.595 vs PYF 0.655 on same rows",
        "window": "2019-2025 lagged test subset",
        "next_use": "descriptive RB slice context only; stop PFR-specific formula testing",
        "source_use_gate": "review-only source sidecar preserved; no broad PFR promotion",
        "caveat": "did not add enough beyond PYF or multi-year production",
    },
    {
        "ingredient": "ffopportunity expected fantasy points",
        "status": "PARTIAL_WINDOW_PROMISING",
        "best_result": "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10 Spearman 0.790",
        "window": "2022-2025 partial modern window",
        "next_use": "preserve as partial-window benchmark; retest only if coverage expands",
        "source_use_gate": "review-only partial sidecar",
        "caveat": "not full-history comparable; component trailed PYF same rows",
    },
    {
        "ingredient": "NGS",
        "status": "PARTIAL_WINDOW_PROMISING",
        "best_result": "NGS combinations reached about 0.758 on sparse partial rows",
        "window": "2022-2025 partial modern window",
        "next_use": "partial-window interaction context only unless coverage improves",
        "source_use_gate": "review-only partial sidecar",
        "caveat": "coverage is too narrow for plateau claim",
    },
    {
        "ingredient": "EPA / opportunity",
        "status": "INTERACTION_CONTEXT",
        "best_result": "EPA-only formula x ingredient 0.747 full-history; EPA+ffop combo 0.789 partial",
        "window": "2013-2025 sidecar, partial combos when paired with ffop/NGS",
        "next_use": "bounded interaction context; no EPA-only branch",
        "source_use_gate": "review-only public nflfastR/nflverse source",
        "caveat": "core EPA signal trailed current formula plateau",
    },
    {
        "ingredient": "receiving opportunity",
        "status": "INTERACTION_CONTEXT",
        "best_result": "full-history formula x ingredient tied 0.755; partial receiving+ffop combo 0.790",
        "window": "2013-2025 sidecar, partial combos when paired with ffop/NGS",
        "next_use": "bounded interaction and slice context only",
        "source_use_gate": "review-only public nflverse/nflfastR source",
        "caveat": "no full-history receiving opportunity result beat 0.755",
    },
    {
        "ingredient": "snap/depth role",
        "status": "BROAD_WINDOW_ADDITIVE_SIGNAL",
        "best_result": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100 Spearman 0.763",
        "window": "2014-2025 broad window; 5,122 rows",
        "next_use": "best non-partial additive ingredient; keep as benchmark and possible future combo anchor",
        "source_use_gate": "review-only public no-key nflverse assets",
        "caveat": "not production; full-history lift was only 0.758",
    },
    {
        "ingredient": "injury availability",
        "status": "GUARDRAIL_CONTEXT",
        "best_result": "best broad/full formula x ingredient 0.757; partial ffop combo 0.789",
        "window": "lagged public nflverse availability sidecar",
        "next_use": "availability caveat and slice context only",
        "source_use_gate": "review-only; no injury prediction",
        "caveat": "did not beat snap/depth 0.763",
    },
    {
        "ingredient": "market/ADP",
        "status": "BLOCKED_FOR_HISTORICAL",
        "best_result": "no sidecar or tests; 220 sources ledgered but as-of gate failed",
        "window": "blocked",
        "next_use": "display-only/current awareness or future acquisition plan",
        "source_use_gate": "historical/as-of proof missing",
        "caveat": "current-only market cannot be historical formula input",
    },
    {
        "ingredient": "rookie/draft capital",
        "status": "GUARDRAIL_CONTEXT",
        "best_result": "best combo 0.744 on positive drafted-evidence subset",
        "window": "positive drafted-evidence subset, 4,044 joined rows",
        "next_use": "rookie/sparse-history context; no new draft branch without dedicated authorization",
        "source_use_gate": "positive draft evidence only; CFBD and UDFA inference blocked",
        "caveat": "not full-history or broad-window comparable",
    },
    {
        "ingredient": "age/lifecycle",
        "status": "ADDITIVE_SIGNAL",
        "best_result": "older/late lifecycle captured 31.3% PYF false positives; young/early captured 49.0% PYF false negatives",
        "window": "2013-2025 review-only sidecar",
        "next_use": "formula-family context, diagnostics, and guardrail slices",
        "source_use_gate": "review-only sidecar; not direct ranking input",
        "caveat": "can over-penalize older elite producers or over-reward young sparse-history players",
    },
    {
        "ingredient": "role archetype",
        "status": "GUARDRAIL_CONTEXT",
        "best_result": "high-volume archetypes held 81.8% of PYF false positives; sparse rows startable rate 3.3%",
        "window": "2013-2025 review-only receipts",
        "next_use": "miss taxonomy, guardrail context, and future slice reporting",
        "source_use_gate": "review-only only; not formula weight",
        "caveat": "does not replace PYF and can create false confidence if overused",
    },
    {
        "ingredient": "confidence cap",
        "status": "GUARDRAIL_CONTEXT",
        "best_result": "WR low-confidence caution rows: 27/28 non-startable; no measurable signal beyond PYF",
        "window": "2013-2025 review-only receipts",
        "next_use": "caution/coverage context only",
        "source_use_gate": "review-only only",
        "caveat": "not a formula or ranking feature",
    },
]


scoreboard_rows = [
    {
        "scoreboard_window": "full_history_comparable",
        "best_candidate_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100",
        "ingredient_set": "snap/depth role depth stability",
        "formula_seed": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE",
        "rows": "5518",
        "seasons": "2013-2025",
        "spearman": "0.758",
        "pyf_same_row_baseline": "0.741",
        "formula_alone_same_row_baseline": "0.755",
        "current_best_delta": "0.003",
        "snap_depth_0763_delta": "",
        "caveats": "Full-history lift is only about +0.003 over the accepted 0.755 plateau, not a material break.",
    },
    {
        "scoreboard_window": "broad_window_comparable",
        "best_candidate_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100",
        "ingredient_set": "snap/depth role low-snap stability",
        "formula_seed": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE",
        "rows": "5122",
        "seasons": "2014-2025",
        "spearman": "0.763",
        "pyf_same_row_baseline": "0.744",
        "formula_alone_same_row_baseline": "0.755",
        "current_best_delta": "0.008",
        "snap_depth_0763_delta": "0.000",
        "caveats": "Accepted broad-window reference; tied variants exist at 0.763. Missing earliest full-history coverage.",
    },
    {
        "scoreboard_window": "partial_window_modern",
        "best_candidate_id": "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10",
        "ingredient_set": "ffopportunity",
        "formula_seed": "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD",
        "rows": "1740",
        "seasons": "2022-2025",
        "spearman": "0.790",
        "pyf_same_row_baseline": "0.779",
        "formula_alone_same_row_baseline": "0.789",
        "current_best_delta": "0.035",
        "snap_depth_0763_delta": "",
        "caveats": "Partial-window only; does not prove a full-history plateau break or justify ranking simulation.",
    },
]


lane_priority_rows = [
    {
        "candidate_lane": "Team Offensive Environment Sidecar V1",
        "rank": "1",
        "likely_accuracy_upside": "medium_high",
        "source_availability": "likely_public_nflverse_nflfastR_team_or_pbp_aggregates",
        "historical_asof_safety": "good_if_prior_season_lagged",
        "coverage": "likely_2013_2025_or_near_full_history",
        "join_feasibility": "high_team_season_to_player_season",
        "leakage_risk": "low_to_medium_with_strict_N_to_Nplus1_lag",
        "governance_bloat_risk": "medium",
        "expected_effort": "medium",
        "could_beat_0763": "plausible",
        "could_help_partial_0790": "possible_as_context",
        "better_than_stopping": "yes",
        "decision": "SELECTED_NEXT",
        "rationale": "Adds team/offensive context that is independent from player prior production and may explain role/opportunity changes without paid data.",
    },
    {
        "candidate_lane": "Participation / Personnel / Pressure Context Sidecar V1",
        "rank": "2",
        "likely_accuracy_upside": "medium_high",
        "source_availability": "partial_or_uncertain_public_sources",
        "historical_asof_safety": "needs_strict_gate",
        "coverage": "likely_partial",
        "join_feasibility": "medium",
        "leakage_risk": "medium_high",
        "governance_bloat_risk": "high",
        "expected_effort": "high",
        "could_beat_0763": "possible_but_not_first",
        "could_help_partial_0790": "possible",
        "better_than_stopping": "yes_later",
        "decision": "PARK_AFTER_TEAM_CONTEXT",
        "rationale": "Potentially valuable, but easier to confuse with route/participation semantics and likely less complete than team context.",
    },
    {
        "candidate_lane": "Rookie Sparse-History Dedicated Model Design V1",
        "rank": "3",
        "likely_accuracy_upside": "slice_specific_medium",
        "source_availability": "existing_draft_age_role_context",
        "historical_asof_safety": "good_for_static_draft_after_draft_year",
        "coverage": "subset_only",
        "join_feasibility": "medium",
        "leakage_risk": "low_for_draft_high_for_prospect_if_added",
        "governance_bloat_risk": "medium",
        "expected_effort": "medium",
        "could_beat_0763": "unlikely_overall_possible_sparse_slice",
        "could_help_partial_0790": "not_primary",
        "better_than_stopping": "yes_for_rookie_lane_only",
        "decision": "PARK_FOR_DEDICATED_AUTHORIZATION",
        "rationale": "Useful for sparse-history slices but not the best immediate overall accuracy lane.",
    },
    {
        "candidate_lane": "Historical Market / ADP Acquisition Plan V1",
        "rank": "4",
        "likely_accuracy_upside": "high_if_true_asof_source_found",
        "source_availability": "not_yet_proven",
        "historical_asof_safety": "blocked_until_proven",
        "coverage": "unknown",
        "join_feasibility": "unknown",
        "leakage_risk": "high_until_asof_proof",
        "governance_bloat_risk": "medium",
        "expected_effort": "medium_high",
        "could_beat_0763": "possible_if_acquired",
        "could_help_partial_0790": "possible",
        "better_than_stopping": "only_if_specific_asof_source_identified",
        "decision": "PARK",
        "rationale": "Market is high-value but current sources failed the historical/as-of gate.",
    },
    {
        "candidate_lane": "FTN Charting Partial Diagnostic Sidecar V1",
        "rank": "5",
        "likely_accuracy_upside": "medium_partial",
        "source_availability": "likely_partial_2022_plus_if_present",
        "historical_asof_safety": "needs_gate",
        "coverage": "partial_modern",
        "join_feasibility": "medium",
        "leakage_risk": "medium",
        "governance_bloat_risk": "high",
        "expected_effort": "high",
        "could_beat_0763": "not_full_history",
        "could_help_partial_0790": "possible",
        "better_than_stopping": "later_only",
        "decision": "PARK",
        "rationale": "Likely limited to partial-window diagnostics and not enough to resolve the full-history plateau.",
    },
    {
        "candidate_lane": "Second Ingredient Combination Test Around Best Broad-Window Candidates V1",
        "rank": "6",
        "likely_accuracy_upside": "low_medium",
        "source_availability": "already_available",
        "historical_asof_safety": "already_gated",
        "coverage": "broad_window",
        "join_feasibility": "high",
        "leakage_risk": "low",
        "governance_bloat_risk": "medium_high",
        "expected_effort": "medium",
        "could_beat_0763": "unlikely_without_new_data",
        "could_help_partial_0790": "unlikely",
        "better_than_stopping": "not_now",
        "decision": "DO_NOT_SELECT",
        "rationale": "Would mostly retest the same ingredient combinations that have already plateaued.",
    },
    {
        "candidate_lane": "Batch Canonicalization / Merge Review V1",
        "rank": "7",
        "likely_accuracy_upside": "none_direct",
        "source_availability": "local_packets_available",
        "historical_asof_safety": "not_applicable",
        "coverage": "not_applicable",
        "join_feasibility": "not_applicable",
        "leakage_risk": "low",
        "governance_bloat_risk": "low",
        "expected_effort": "medium",
        "could_beat_0763": "no",
        "could_help_partial_0790": "no",
        "better_than_stopping": "yes_for_housekeeping_not_accuracy",
        "decision": "PARK_UNTIL_MODEL_DECISION",
        "rationale": "Useful soon, but the requested decision is the next accuracy/data lane.",
    },
    {
        "candidate_lane": "Stop and wait for user review",
        "rank": "8",
        "likely_accuracy_upside": "none",
        "source_availability": "not_applicable",
        "historical_asof_safety": "not_applicable",
        "coverage": "not_applicable",
        "join_feasibility": "not_applicable",
        "leakage_risk": "low",
        "governance_bloat_risk": "low",
        "expected_effort": "none",
        "could_beat_0763": "no",
        "could_help_partial_0790": "no",
        "better_than_stopping": "no_selected_lane_exists",
        "decision": "NOT_SELECTED",
        "rationale": "A viable public-data sidecar lane remains.",
    },
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(
        "INGREDIENT_STATUS_AFTER_ALL_UPGRADES.csv",
        ingredient_status_rows,
        [
            "ingredient",
            "status",
            "best_result",
            "window",
            "next_use",
            "source_use_gate",
            "caveat",
        ],
    )
    write_csv(
        "INGREDIENT_SCOREBOARD_BY_WINDOW.csv",
        scoreboard_rows,
        [
            "scoreboard_window",
            "best_candidate_id",
            "ingredient_set",
            "formula_seed",
            "rows",
            "seasons",
            "spearman",
            "pyf_same_row_baseline",
            "formula_alone_same_row_baseline",
            "current_best_delta",
            "snap_depth_0763_delta",
            "caveats",
        ],
    )
    write_csv(
        "REMAINING_DATA_LANE_PRIORITY_MATRIX.csv",
        lane_priority_rows,
        [
            "candidate_lane",
            "rank",
            "likely_accuracy_upside",
            "source_availability",
            "historical_asof_safety",
            "coverage",
            "join_feasibility",
            "leakage_risk",
            "governance_bloat_risk",
            "expected_effort",
            "could_beat_0763",
            "could_help_partial_0790",
            "better_than_stopping",
            "decision",
            "rationale",
        ],
    )

    report = f"""
# Ingredient Combination Plateau Review / Next Data Decision V1 Report

Verdict: `{VERDICT}`

Artifact path: `{OUT_DIR}`

Remote HQ verified: `{REMOTE_HEAD}`

Prior rookie/draft commit verified: `{PRIOR_ROOKIE_COMMIT}`

## Lanes Included

This review consolidates PFR RB broken tackles, ffopportunity / NGS autonomous V2, EPA/opportunity, receiving opportunity, snap/depth role, point-in-time injury availability, historical market/ADP gate, rookie/draft capital, age/lifecycle, role archetype, confidence cap, the full review-only Gauntlet, clustering audit, and diverse champion refinement.

## Plateau Decision

Ingredient-combination work has reached a current plateau with the available ingredients. The best full-history result is `0.758`, only about `+0.003` over the accepted `0.755` review-only plateau. The best broad-window result remains snap/depth at `0.763` across `2014-2025`. The strongest `0.790` results remain partial-window modern results from `2022-2025` and are not full-history comparable.

The evidence supports a data-upgrade pivot, not more same-ingredient formula tuning or ranking simulation.

## Best Scoreboards

- Full-history: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100`, Spearman `0.758`, rows `5,518`, seasons `2013-2025`.
- Broad-window: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100`, Spearman `0.763`, rows `5,122`, seasons `2014-2025`.
- Partial-window: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPORTUNITY_PCT10`, Spearman `0.790`, rows `1,740`, seasons `2022-2025`.

## Next Lane

Recommended next lane: `{NEXT_LANE}`.

Reason: team/offensive environment is the best remaining public-data path with plausible accuracy upside, likely full-history or near-full-history coverage, and a clean lagged player-season join path through team-season context. It is more likely to add independent signal than another bounded combination pass with already-tested ingredients, and it has lower immediate leakage/source risk than market/ADP, FTN charting, participation/personnel/pressure, or paid data.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime changes remain blocked.
- Source promotion remains blocked.
- Review-only ranking simulation remains blocked.
- Push/merge was not performed.
- Current-best formula candidates are not approved for production use.
"""
    # Correct typo while keeping the report generated from one source.
    report = report.replace("FFOPORTUNITY", "FFOPPORTUNITY")
    write_text("INGREDIENT_COMBINATION_PLATEAU_REVIEW_NEXT_DATA_DECISION_V1_REPORT.md", report)

    plateau = """
# Ingredient Combination Plateau Decision

Decision: `CURRENT_INGREDIENT_COMBINATION_PLATEAU_CONFIRMED`

## Findings

- No full-history result materially beat the accepted `0.755` review-only plateau.
- No broad-window result materially beat the snap/depth `0.763` reference on comparable rows.
- No partial-window result materially beat the accepted `0.790` modern-window reference on comparable rows.
- Repeated formula-combo gains are small and mostly cluster around multi-year production plus role, age/lifecycle, and snap/depth context.
- Stronger modern partial-window ingredients remain promising but not full-history comparable.

## Decision

Pause same-ingredient formula-combination search. The next accuracy move should add a new clean sidecar rather than retune existing ingredients.
"""
    write_text("INGREDIENT_COMBINATION_PLATEAU_DECISION.md", plateau)

    next_decision = f"""
# Next Data Or Model Lane Decision

Decision: `{NEXT_LANE}`

## Why This Lane

Team offensive environment can plausibly explain player opportunity changes that prior production, role archetype, and snap/depth only approximate. It should be built as lagged review-only team-season context, joined to player-season rows only for N+1 target tests.

## Why Not The Alternatives

- A second ingredient-combination pass risks retesting plateaued ingredients.
- Participation/personnel/pressure has higher semantic and coverage risk.
- FTN charting is likely partial-window diagnostic only.
- Historical Market / ADP remains blocked until true row-level as-of proof exists.
- Rookie sparse-history model design is useful later but narrower than the overall formula plateau question.
- Batch canonicalization is useful housekeeping, not the next accuracy/data lane.

## Required Guardrails For The Next Lane

- No same-season team context as historical prediction input.
- No current/future context.
- No source promotion.
- No production/model-use.
- No ranking integration.
- No app/runtime change.
"""
    write_text("NEXT_DATA_OR_MODEL_LANE_DECISION.md", next_decision)

    ranking_blocker = """
# Ranking Simulation Blocker Review

Decision: `REVIEW_ONLY_RANKING_SIMULATION_NOT_JUSTIFIED`

Ranking simulation remains blocked because the best full-history lift is only `0.758`, the best broad-window lift is `0.763`, and the `0.790` results are partial-window modern results. These are useful review-only findings, but they do not clear the bar for a ranking simulation or production-adjacent board projection.

Ranking simulation can be reconsidered only after a new ingredient sidecar provides a material full-history or broad-window lift with clean same-row baselines, leakage/as-of proof, source/use-gate status, and stable slice behavior.
"""
    write_text("RANKING_SIMULATION_BLOCKER_REVIEW.md", ranking_blocker)

    stop_testing = """
# Ingredients To Stop Testing

- PFR RB broken tackles as a formula ingredient. Preserve only descriptive RB slice context.
- Market/ADP for historical formula testing until row-level historical/as-of proof exists.
- Confidence cap as a formula/ranking feature. Preserve only caution/coverage context.
- EPA-only formula branches.
- Receiving-opportunity-only formula branches.
- Draft-capital formula branches, unless a future dedicated rookie/sparse-history lane is authorized.
- Same-ingredient weight tweaking around the current multi-year production family.
- SportsDataIO, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, and current-only ADP remain blocked.
"""
    write_text("INGREDIENTS_TO_STOP_TESTING.md", stop_testing)

    keep_context = """
# Ingredients To Keep As Context

- Age/lifecycle: formula-family context, prior-decline and breakout-window slices.
- Role archetype: miss taxonomy, guardrail context, and future slice reporting.
- Confidence cap: caution/coverage context only.
- Injury availability: availability caveat and guardrail context only.
- EPA/opportunity: interaction context only.
- Receiving opportunity: interaction context only.
- PFR RB broken tackles: descriptive RB slice context only.
- Rookie/draft capital: rookie, sparse-history, and early-career context only.
"""
    write_text("INGREDIENTS_TO_KEEP_AS_CONTEXT.md", keep_context)

    future_testing = """
# Ingredients Worth Future Testing

- Team offensive environment, selected as the next lane.
- Snap/depth role as a benchmark and possible future combo anchor if paired with a new clean data family.
- ffopportunity and NGS only if coverage can be expanded or clearly marked as partial-window benchmarks.
- Rookie/draft capital only in a dedicated sparse-history or rookie model design lane.
- Participation/personnel/pressure only after team environment, and only if route-like claims are blocked.
"""
    write_text("INGREDIENTS_WORTH_FUTURE_TESTING.md", future_testing)

    source_trace = f"""
# Ingredient Combination Source Trace

## Current Lane

- Remote HQ verified: `{REMOTE_HEAD}`
- Prior rookie/draft commit verified: `{PRIOR_ROOKIE_COMMIT}`

## Prior Review Inputs

- `docs/hq/model/rookie_draft_capital_data_mart_join_component_test_v1_20260709/`
- `docs/hq/model/historical_market_adp_source_gate_data_mart_join_v1_20260709/`
- `docs/hq/master/ingredient_scoreboard_normalization_best_candidate_consolidation_v1_20260709/`
- `docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709/`
- `docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709/`
- `docs/hq/model/nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709/`
- `docs/hq/model/nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709/`
- `docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/`
- `C:/NWR/Niners-War-Room-pfr-rb-broken-tackle-data-mart-join-component-test-v1-20260709/docs/hq/data_hygiene/pfr_rb_broken_tackle_data_mart_join_component_test_v1_20260709/`
- `C:/NWR/Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709/docs/hq/model/full_review_only_formula_gauntlet_candidate_arena_v1_20260709/`
- `C:/NWR/Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709/docs/hq/model/gauntlet_candidate_diversity_clustering_audit_v1_20260709/`
- `C:/NWR/Niners-War-Room-diverse-champion-refinement-predeclared-execution-v1-20260709/docs/hq/model/diverse_champion_refinement_predeclared_execution_v1_20260709/`
- `C:/NWR/Niners-War-Room-age-lifecycle-master-review-v1-20260709/docs/hq/master/age_lifecycle_master_review_v1_20260709/`

## Safety Trace

No formula run, broad Gauntlet, dynamic tuning, ranking simulation, production/model-use, rankings integration, app/runtime change, source promotion, SportsDataIO, paid/API/free-trial/API-key source, canonical `local_exports` mutation, push, or merge occurred in this lane.
"""
    write_text("INGREDIENT_COMBINATION_SOURCE_TRACE.md", source_trace)


if __name__ == "__main__":
    main()
