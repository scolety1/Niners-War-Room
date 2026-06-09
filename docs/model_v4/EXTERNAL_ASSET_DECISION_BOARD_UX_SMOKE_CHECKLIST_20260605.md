# External Asset And Decision Board UX Smoke Checklist

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: provide a manual smoke-test checklist for External Asset Reviews and
Decision Board review-only framing before any formula work. This checklist
verifies source disclosure, warning visibility, receipt/traceability access,
market display-only framing, and blocked-use language. It does not tune
formulas, change generated outputs, mutate active app state, or make trade, cut,
keep, draft, buy, sell, defer, target, or start/sit recommendations.

## Evidence Sources

- External Asset Reviews UI: `app/pages/04_trade_central.py`
- Decision-facing War Board UI: `app/pages/03_war_board.py`
- External Asset Review service:
  `src/services/model_v4_sprint14c_trade_review_service.py::build_trade_review_outputs()`
- Decision Board service:
  `src/services/model_v4_sprint14f_june15_decision_board_service.py::build_june15_decision_board_outputs()`
- External asset value source:
  `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv`
- External asset score column: `dynasty_asset_value_review_score`
- Roster-pressure source:
  `local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv`
- Roster-pressure score column: `pressure_score`
- Decision Board rows:
  `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv`
- Decision Board receipts:
  `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_receipts.csv`
- Decision Board components:
  `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_component_rows.csv`
- Decision Board warnings:
  `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_warnings.csv`
- Supporting audits:
  `docs/model_v4/EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md` and
  `docs/model_v4/DECISION_BOARD_COHERENCE_AUDIT_20260605.md`

## Setup

1. Launch the app using the normal local Streamlit workflow.
2. Open `External Asset Reviews`.
3. Open `War Board` for the decision-facing surface and `Decision Snapshot`.
4. Record the active pack caption, timestamp, browser, and tester initials.
5. Keep this pass observational. Do not edit active rankings, My Team, War
   Board, readiness gates, app promotion, active data packs, generated outputs,
   mock drafts, or user-entered draft state.

## External Asset Reviews Load Checks

| Check | Steps | Expected Result |
|---|---|---|
| Page load | Open `External Asset Reviews` | Page title, active pack caption, trust banner, and review-only copy are visible |
| Metrics | Inspect `Roster Reviews`, `External Context`, and `Snapshot` | Counts load without generating outputs or changing readiness |
| Detail player | Use `Inspect trade-context player` | Detail panel shows model value, market context as display-only, confidence/risk, warning groups, and source pointer |
| Tab labels | Inspect tabs | `Roster Context`, `External Asset Context`, `Market Context`, and `Context Drill-Down` are visible |
| Review framing | Read captions | Copy says context is for review and does not auto-send offers |

Fail the smoke test if the surface creates or implies a final offer,
acquisition call, buy call, sell call, cut call, draft call, defer call, or
target recommendation.

## External Asset Source Disclosure Checks

For external asset rows such as `Trey McBride`, `Puka Nacua`,
`Jaxon Smith-Njigba`, `Christian McCaffrey`, `Josh Allen`,
`Jonathan Taylor`, `Bijan Robinson`, `Ja'Marr Chase`, `Jahmyr Gibbs`, and
`Amon-Ra St. Brown`, verify:

- Model value traces to `dynasty_asset_value_review_score` through current
  dynasty asset value context.
- Lineage is `review_v4_dynasty_asset` where source disclosure is surfaced.
- Allowed use is review-only external asset context.
- Blocked use prevents trade offers, buy calls, acquisition calls, and final
  recommendations.
- Warnings such as source-limited route/snap evidence, age-window context,
  1QB context, no-premium TE context, or identity/source review remain visible.
- Market context is display-only and does not populate private value.

## Roster Context And Market Context Checks

| Surface | Smoke Check |
|---|---|
| `Roster Context` | `Roster Review Group` filter narrows rows without changing model value, market context, confidence, or risk |
| `External Asset Context` | `External Review Group` filter narrows opponent-player context rows without creating targets or offers |
| `Market Context` | `Market Gap Signal`, `Normalized Market Gap`, and `Market Context Finder` are labeled as comparison/display context only |
| `How to read Market Gap` | Explains missing league rank/ADP as partial context, not a private-value input |
| `Context Drill-Down` | Shows context pairings as conversation-shape drilldowns only; no offer is created |
| `Advanced: pick path audit` | Pick paths remain audit context and do not create pick-equivalence offers |

Fail the smoke test if league rank, ADP, market reference score, market gap,
context pairing, or pick path audit changes private model value or becomes an
instruction.

## Decision Board Surface Checks

The generated Decision Board artifact is a review-only aggregate board. In the
current app, the decision-facing surface to smoke manually is War Board
`Decision Snapshot`, ranking surfaces, `Why Ranked Here`, and advanced receipt
sections.

| Check | Steps | Expected Result |
|---|---|---|
| War Board load | Open `War Board` | Review-only trust banner and `Model Value is stats-first private value; Trade Market is liquidity only` copy are visible |
| Decision Snapshot | Inspect `Top Ranked`, `Action Queue`, and `Model vs Market` | Snapshot rows are prompts only; legacy labels are quarantined where shown |
| Ranking Surface | Toggle `Pure Model Value`, `Keeper Decision`, `Trade/Liquidity`, and `Forced-Release Pain` | Captions disclose rank source, intended use, and sort; surfaces do not mutate active rankings |
| Why Ranked Here | Select a row and open `Why Ranked Here` | Compact receipt exposes model drivers, drags/review flags, source warnings, and market context as liquidity only |
| Advanced receipts | Open `Advanced: full receipt rows` | Full receipt rows remain reachable for selected player |
| Source audit | Open `Advanced: score source audit` if present | Selected-pack/newer-preview source status is disclosed |

## Decision Board Artifact Traceability

When auditing generated Decision Board outputs or an exported packet, verify:

- `june15_decision_board_review_rows.csv` has 105 decision rows.
- `june15_decision_board_receipts.csv` has 105 receipt rows.
- `june15_decision_board_component_rows.csv` has 315 component rows.
- `june15_decision_board_warnings.csv` has warning rows for explicit follow-up.
- Decision areas include `rookie_pick_window_context`,
  `roster_pressure_trade_context`, and `pick_trade_defer_context`.
- Every decision row allows only
  `review_only_june15_decision_context_not_final_action`.
- Every decision row blocks
  `do_not_use_as_final_cut_keep_trade_or_draft_recommendation`.
- Summary guardrails keep `final_recommendations_created`,
  `war_board_changed`, `my_team_changed`, `active_rankings_changed`, and
  `readiness_unlocked` false.

## Decision Board Sentinel Rows

| Entity | Area | Expected Smoke Result |
|---|---|---|
| `2026 1.03` | `pick_trade_defer_context` | Pick score matches the admitted pick inventory context; defer premium remains review-only |
| `2026 5.04` | `pick_trade_defer_context` | Source score remains blank/manual-only; no exact model baseline or equivalence is invented |
| `Kaleb Johnson` | `roster_pressure_trade_context` | Pressure source is visible; row prompts review before any human cut or trade action |
| `Luke McCaffrey` | `roster_pressure_trade_context` | Trade-market-before-cut context remains a review prompt, not a cut/sell call |
| `Jeremiyah Love` | `rookie_pick_window_context` | Rookie candidate score traces to rookie pick candidate context and stays draft-review only |
| `Makai Lemon` | `rookie_pick_window_context` | Gap context stays review-only and warning-aware |
| `Ja'Kobi Lane` | `rookie_pick_window_context` | Tier-gap context stays review-only and warning-aware |

## Review-Only Language Checks

- External Asset Reviews must say context is review-only and no offer is created.
- Market context must be described as liquidity/comparison/display context only.
- Decision Snapshot and ranking surfaces must remain prompts for human review,
  not final actions.
- The words buy, sell, target, trade-for, drop, cut, keep, draft, and defer may
  appear in legacy compatibility fields, blocked-use text, or guardrail text,
  but visible main-path copy must not convert them into final instructions.
- Compatibility fallback CSVs under `local_exports/model_v4/trade_review/latest`
  may still contain stale naming such as `trade_for_review_band` or
  `elite_target_review`; treat those as compatibility-only evidence until an
  output refresh is allowed.

## Fail Conditions

Stop and document a bug if any of these are observed:

- External Asset Reviews creates an offer, package, acquisition call, buy call,
  sell call, or target recommendation.
- Decision Board or War Board rows become final cut, keep, trade, draft, buy,
  sell, defer, target, or start/sit recommendations.
- `2026 5.04` gets an exact score or pick baseline where the audit says none
  exists.
- Market, ADP, rankings, projections, consensus, startup, market-gap, or
  trade-calculator context populates private model value.
- Warning groups, blocked-use fields, receipts, source paths, source columns, or
  lineage fields are hidden on the review path.
- A filter or surface toggle mutates active rankings, My Team, War Board,
  readiness gates, app promotion, active data packs, generated outputs, mock
  drafts, or user-entered draft state.

## Evidence Capture Worksheet

| Field | Tester Entry |
|---|---|
| Date/time |  |
| App URL |  |
| Active pack caption |  |
| Browser |  |
| External Asset Reviews loaded | Pass / Fail |
| External asset source disclosure pass | Pass / Fail |
| Market display-only pass | Pass / Fail |
| Context Drill-Down review-only pass | Pass / Fail |
| War Board Decision Snapshot pass | Pass / Fail |
| Why Ranked Here receipts pass | Pass / Fail |
| Decision Board artifact counts pass | Pass / Fail |
| `2026 5.04` manual-only pass | Pass / Fail |
| No final recommendation language | Pass / Fail |
| Notes/screenshots |  |

## Non-Goals

- Do not tune formulas from this checklist.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated outputs, mock drafts, or user-entered
  draft state.
- Do not use this checklist as proof the model is ready for money decisions. It
  is a UX/source-disclosure and review-only-framing smoke test.
