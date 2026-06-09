# Pick Value Ladder Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: inspect `2026 1.03`, `2026 1.04`, `2026 2.04`,
`2026 2.08`, and `2026 5.04` against admitted pick baselines and nearby
ladder rows. This report is evidence only. It does not change pick baselines,
startup-slot conversion, rookie weights, model weights, VORP, replacement
formulas, confidence caps, generated outputs, Draft Room state, War Board
state, user-entered draft state, or recommendation logic.

## Sources

| Surface | Source Path | Score Column | Role |
|---|---|---|---|
| Pick value baselines | `local_exports/model_v4/pick_values/latest/pick_value_baselines_review.csv` | `pick_value_review_score` | Admitted pick ladder baseline rows. |
| Niners pick inventory | `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv` | `pick_value_review_score` | Owned-pick inventory and baseline-match status. |
| Rookie Pick Decision Lab | `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv` | `pick_value_score` | Review-only pick context and manual questions. |
| Pick decision comparisons | `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_compare_rows.csv` | `score_gap_to_pick` | Internal model-neighborhood context only. |

Baseline allowed use is
`review_only_pick_value_baseline_not_trade_recommendation`. Inventory allowed
use is `review_only_pick_inventory_not_trade_recommendation`. Decision Lab
allowed use is `review_only_rookie_pick_decision_lab_not_final_selection`.

## Owned Pick Baseline Check

| Pick | Baseline Score | Inventory Score | Baseline Match | Tier | Decision Score | Confidence | Review Label | Equivalence Guardrail |
|---|---:|---:|---|---|---:|---|---|---|
| 2026 1.03 | 93.6 | 93.6 | matched_pick_value_baseline | early_first | 93.6 | top_cluster_has_missing_evidence_review | review_defer_context | internal_model_neighbor_only_not_one_for_one_trade_equivalent |
| 2026 1.04 | 90.4 | 90.4 | matched_pick_value_baseline | mid_first | 90.4 | top_cluster_has_missing_evidence_review | review_defer_context | internal_model_neighbor_only_not_one_for_one_trade_equivalent |
| 2026 2.04 | 71.4 | 71.4 | matched_pick_value_baseline | second_round | 71.4 | top_cluster_has_missing_evidence_review | review_defer_context | nearby_model_value_not_trade_equivalence |
| 2026 2.08 | 58.6 | 58.6 | matched_pick_value_baseline | second_round | 58.6 | top_cluster_has_missing_evidence_review | review_rookie_vs_veteran | nearby_model_value_not_trade_equivalence |
| 2026 5.04 | missing | blank | missing_pick_value_baseline | manual_only_no_exact_model_baseline | blank | manual_only_no_exact_model_baseline | manual_only_no_exact_model_baseline | no_exact_equivalence_without_pick_baseline |

All five inventory rows carry
`do_not_use_as_pick_trade_recommendation_or_offer`. All five Decision Lab rows
carry `do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation`.

## Nearby Admitted Ladder Rows

| Pick | Score | Tier | Allowed Use | Confidence | Warning Flags |
|---|---:|---|---|---|---|
| 2026 1.01 | 100.0 | early_first | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 1.02 | 96.8 | early_first | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 1.03 | 93.6 | early_first | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 1.04 | 90.4 | mid_first | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 1.05 | 87.2 | mid_first | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 2.03 | 74.6 | second_round | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 2.04 | 71.4 | second_round | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 2.05 | 68.2 | second_round | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 2.07 | 61.8 | second_round | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 2.08 | 58.6 | second_round | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 2.09 | 55.4 | second_round | review_only_pick_value_baseline_not_trade_recommendation | review_only_pick_baseline_no_market_input | heuristic_pick_curve_requires_audit |
| 2026 5.03 | missing | manual_only_no_exact_model_baseline | no admitted baseline row | missing baseline | manual_only_no_exact_model_baseline |
| 2026 5.04 | missing | manual_only_no_exact_model_baseline | no admitted baseline row | missing baseline | manual_only_no_exact_model_baseline |
| 2026 5.05 | missing | manual_only_no_exact_model_baseline | no admitted baseline row | missing baseline | manual_only_no_exact_model_baseline |

## Decision Lab Context

| Pick | Candidate Context | First Rookie Context | First Internal Neighbor | Manual Pick-Value Question | Market/Equivalence Context |
|---|---|---|---|---|---|
| 2026 1.03 | Jeremiyah Love RB (75.3111) | Jeremiyah Love RB (75.3111) | Trey McBride TE (87.4776) | Is the candidate cluster close enough to the owned pick value to deserve manual review? | Shown near elite/current assets by internal model score only; not a claim one pick can buy those players. |
| 2026 1.04 | Jeremiyah Love RB (75.3111) | Jeremiyah Love RB (75.3111) | Trey McBride TE (87.4776) | Is the candidate cluster close enough to the owned pick value to deserve manual review? | Shown near elite/current assets by internal model score only; not a claim one pick can buy those players. |
| 2026 2.04 | Antonio Williams WR (54.2258) | Antonio Williams WR (54.2258) | Makai Lemon WR (69.2158) | Is the candidate cluster close enough to the owned pick value to deserve manual review? | Nearby assets are internal value neighbors only; verify actual trade market separately. |
| 2026 2.08 | Ja'Kobi Lane WR (49.2653) | Ja'Kobi Lane WR (49.2653) | Josh Jacobs RB (58.5387) | Is the candidate cluster close enough to the owned pick value to deserve manual review? | Nearby assets are internal value neighbors only; verify actual trade market separately. |
| 2026 5.04 | manual_only_no_exact_candidate_fit_context | manual_only_no_exact_model_baseline: inspect the full board manually; no exact candidate cluster or slot equivalence is admitted for this pick. | manual_only_no_exact_model_baseline: inspect the full board manually; no exact candidate cluster or slot equivalence is admitted for this pick. | No admitted exact model baseline exists for this pick; use manual-only watchlist review. | Manual-only pick baseline; no exact trade-market equivalence or package context is admitted. |

## Comparison Row Counts

| Pick | Comparison Rows | Rookie Candidate Rows | Startup/Internal Neighbor Rows | Blank Score Gaps |
|---|---:|---:|---:|---:|
| 2026 1.03 | 16 | 8 | 8 | 0 |
| 2026 1.04 | 16 | 8 | 8 | 0 |
| 2026 2.04 | 16 | 8 | 8 | 0 |
| 2026 2.08 | 16 | 8 | 8 | 0 |
| 2026 5.04 | 8 | 8 | 0 | 8 |

The `2026 5.04` comparison rows intentionally have blank `score_gap_to_pick`
because there is no admitted exact model baseline for that pick.

## Review Observations

- The admitted ladder is monotonic across the inspected neighborhoods:
  `1.01` 100.0, `1.02` 96.8, `1.03` 93.6, `1.04` 90.4, `1.05` 87.2,
  then `2.03` 74.6, `2.04` 71.4, `2.05` 68.2, `2.07` 61.8, `2.08` 58.6,
  and `2.09` 55.4.
- `2026 1.03` and `2026 1.04` are premium owned-pick rows by the admitted
  internal ladder, but their warning flags still include
  `heuristic_pick_curve_requires_audit` and final-action blocked use.
- `2026 2.04` and `2026 2.08` have admitted second-round baselines and
  nearby-model-value guardrails; those internal neighbors are context, not
  one-for-one trade equivalence.
- `2026 5.04` remains the sentinel row: no admitted exact baseline row, blank
  numeric score fields, manual-only confidence/tier, and
  `no_exact_equivalence_without_pick_baseline`.

## Non-Goals

- Do not change pick baselines from this report.
- Do not change startup-slot conversion, rookie weights, model weights, VORP,
  replacement formulas, confidence caps, age curves, or market-gap thresholds.
- Do not mutate generated outputs, Draft Room state, War Board state, active
  rankings, My Team, or user-entered draft state.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert review labels or neighborhoods into trade, cut, keep, draft,
  buy, sell, defer, target, or start/sit recommendations.
