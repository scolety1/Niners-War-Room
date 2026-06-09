# Decision Board Coherence Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: trace representative Decision Board rows back to source rows and
receipts, then verify decision areas, warning flags, components, and blocked
use remain review-only. This report is evidence only. It does not mutate
Decision Board outputs, formulas, active rankings, My Team, War Board,
readiness gates, app promotion, active data packs, generated outputs, or
recommendation logic.

## Sources

| Surface | Source Path | Role |
|---|---|---|
| Decision Board rows | `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv` | Aggregate review board rows. |
| Decision Board receipts | `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_receipts.csv` | One receipt pointer per board row. |
| Decision Board components | `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_component_rows.csv` | Three component rows per board row. |
| Decision Board warnings | `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_warnings.csv` | Review warnings for rows needing explicit follow-up. |
| Pick inventory | `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv` | Source rows for pick decision context. |
| Cut/keep pressure | `local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv` | Source rows for roster-pressure decision context. |
| Rookie pick candidates | `local_exports/model_v4/rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv` | Source rows for rookie-window decision context. |

## Board Snapshot

- Decision rows: 105.
- Receipt rows: 105.
- Component rows: 315.
- Warning rows: 54.
- Summary rows: 18.
- Decision-area counts:
  - `rookie_pick_window_context`: 76.
  - `roster_pressure_trade_context`: 24.
  - `pick_trade_defer_context`: 5.
- Allowed use on every decision row:
  `review_only_june15_decision_context_not_final_action`.
- Blocked use on every decision row:
  `do_not_use_as_final_cut_keep_trade_or_draft_recommendation`.
- Guardrail summary values:
  - `final_recommendations_created`: `False`.
  - `war_board_changed`: `False`.
  - `my_team_changed`: `False`.

## Band Distribution

| Primary Review Band | Rows |
|---|---:|
| rookie_candidate_gap_context_review | 39 |
| rookie_candidate_tier_gap_context_review | 25 |
| roster_context_review | 17 |
| rookie_late_watchlist_context_review | 12 |
| depth_liquidity_context_review | 3 |
| future_first_defer_premium_context_review | 2 |
| pick_defer_context_review | 2 |
| core_hold_context_review | 2 |
| roster_pressure_line_review | 1 |
| trade_market_before_cut_context_review | 1 |
| pick_baseline_missing_review | 1 |

## Trace Sample

| Area | Entity | Pick | Band | Source Score | Secondary | Receipt Pointer | Component Values | Warning Codes | Next Step |
|---|---|---|---|---:|---:|---|---|---|---|
| pick_trade_defer_context | 2026 1.03 | 2026 1.03 | future_first_defer_premium_context_review | 93.6 | 6.4 | local_exports\model_v4\pick_trade_defer\latest\niners_pick_inventory_review_rows.csv | primary_review_band=future_first_defer_premium_context_review; source_review_score=93.6; review_priority=100.0 | none | Audit owner risk and premium before any defer discussion. |
| pick_trade_defer_context | 2026 5.04 | 2026 5.04 | pick_baseline_missing_review | blank | blank | local_exports\model_v4\pick_trade_defer\latest\niners_pick_inventory_review_rows.csv | primary_review_band=pick_baseline_missing_review; source_review_score=; review_priority=20.0 | pick_baseline_missing_review | Manual-only: no exact model baseline exists. Do not include in pick-defer, draft, trade, or cut-equivalence math. |
| roster_pressure_trade_context | Kaleb Johnson | blank | roster_pressure_line_review | 53.3477 | 3.0698 | local_exports\model_v4\decision_pressure\latest\cut_keep_pressure_review_rows.csv | primary_review_band=roster_pressure_line_review; source_review_score=53.3477; review_priority=93.3477 | roster_pressure_line_review | Compare trade-away and rookie replacement context before any human cut call. |
| roster_pressure_trade_context | Luke McCaffrey | blank | trade_market_before_cut_context_review | 72.2389 | 16.2148 | local_exports\model_v4\decision_pressure\latest\cut_keep_pressure_review_rows.csv | primary_review_band=trade_market_before_cut_context_review; source_review_score=72.2389; review_priority=87.2389 | none | Inspect liquidity context before any human roster decision. |
| rookie_pick_window_context | Jeremiyah Love | 2026 1.03 | rookie_candidate_tier_gap_context_review | 75.3111 | -18.2889 | local_exports\model_v4\rookie_draft_review\latest\rookie_pick_candidate_review_rows.csv | primary_review_band=rookie_candidate_tier_gap_context_review; source_review_score=75.3111; review_priority=75.3111 | none | Review tier gap and source warnings before draft-room use. |
| rookie_pick_window_context | Makai Lemon | 2026 1.03 | rookie_candidate_gap_context_review | 69.2158 | -24.3842 | local_exports\model_v4\rookie_draft_review\latest\rookie_pick_candidate_review_rows.csv | primary_review_band=rookie_candidate_gap_context_review; source_review_score=69.2158; review_priority=69.1158 | rookie_candidate_gap_context_review | Review gap and warnings before any draft-room use. |
| rookie_pick_window_context | Ja'Kobi Lane | 2026 2.08 | rookie_candidate_tier_gap_context_review | 49.2653 | -9.3347 | local_exports\model_v4\rookie_draft_review\latest\rookie_pick_candidate_review_rows.csv | primary_review_band=rookie_candidate_tier_gap_context_review; source_review_score=49.2653; review_priority=48.1653 | none | Review tier gap and source warnings before draft-room use. |

## Source Match Checks

- `2026 1.03` Decision Board `source_review_score` matches pick inventory
  `pick_value_review_score` 93.6.
- `2026 5.04` Decision Board keeps blank `source_review_score`, matching the
  missing-baseline pick inventory row.
- `Kaleb Johnson` Decision Board `source_review_score` matches cut/keep
  pressure `pressure_score` 53.3477.
- `Luke McCaffrey` Decision Board `source_review_score` matches cut/keep
  pressure `pressure_score` 72.2389.
- `Jeremiyah Love`, `Makai Lemon`, and `Ja'Kobi Lane` Decision Board
  `source_review_score` values match rookie candidate
  `league_format_adjusted_score`.

## Review Observations

- The board is coherent as an aggregate review index: each row has exactly one
  receipt and three components (`primary_review_band`, `source_review_score`,
  `review_priority`).
- Warning rows are not one-for-one with board rows. Several rows are intentionally
  warning-free when their review-only status is already represented by
  `warning_flags`, `allowed_use`, `blocked_use`, and receipts.
- `2026 5.04` is the key safety sentinel: missing source score, missing-baseline
  band, manual-only next step, and no exact-equivalence language.
- Roster-pressure rows use the cut/keep pressure source, while review context can
  also mention trade-away context. This report does not validate trade-market
  realism.

## Non-Goals

- Do not mutate Decision Board outputs from this report.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not turn review labels into final trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendations.
