# Draft Room UX Smoke Checklist

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: provide a manual smoke-test checklist for Draft Room owned picks,
rookie rows, source disclosure, warning groups, and receipt expanders before
any formula work. This checklist does not tune formulas, change generated
outputs, mutate Draft Room state, or make trade, cut, keep, draft, buy, sell,
defer, target, or start/sit recommendations.

## Evidence Sources

- Draft Room UI: `app/pages/06_draft_board.py`
- Draft room service: `src/services/draft_service.py`
- Draft state service: `src/services/draft_state_service.py`
- Rookie board source:
  `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- Rookie board primary score column: `league_format_adjusted_score`
- Rookie raw score column: `prospect_private_value_review_score`
- Rookie receipts:
  `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_receipts.csv`
- Rookie warnings:
  `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_warnings.csv`
- Pick Decision Lab source:
  `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv`
- Pick Decision Lab primary score column: `pick_value_score`
- Pick Decision Lab comparison source:
  `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_compare_rows.csv`
- Pick Decision Lab components:
  `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_component_rows.csv`
- Pick Decision Lab warnings:
  `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_warnings.csv`
- Supporting audits:
  `docs/model_v4/ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`,
  `docs/model_v4/ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`,
  `docs/model_v4/PICK_VALUE_LADDER_AUDIT_20260605.md`, and
  `docs/model_v4/PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md`

## State Safety Setup

1. Launch the app using the normal local Streamlit workflow.
2. Open `Draft Room`.
3. Record the active pack caption, timestamp, browser, and tester initials.
4. Use a review-only browser pass unless you intentionally create a disposable
   mock draft.
5. Do not click `Draft`, `Undo`, `Replace`, `Reset Mock`, `Save Mock`, `Load
   Mock`, `Duplicate Mock`, `Clear Mock`, or any confirmation checkbox while
   testing source disclosure.
6. Do not mutate active rankings, My Team, War Board, readiness gates, app
   promotion, active data packs, generated outputs, or user-entered draft
   state.

## Top-Level Load Checks

| Check | Steps | Expected Result |
|---|---|---|
| Draft Room loads | Open `Draft Room` | Page title, active pack caption, trust banner, and `Rookie Analyzer` section are visible |
| Review progress checklist | Open `Review progress checklist` | It routes the tester through `Owned Pick Decision Lab`, rookie board review, player drilldown, scout context, and `Receipts / Advanced` |
| Rookie metrics | Inspect metrics under `Rookie Analyzer` | Rookie Board, candidate, receipt, and warning counts load without requiring state mutation |
| Review-only framing | Read captions at top of page | Copy frames Draft Room as review-only and separates scoring evidence from non-scoring context |

Fail the smoke test if the page presents any reviewed row as a final draft,
trade, cut, keep, buy, sell, defer, target, or start/sit instruction.

## Owned Pick Decision Lab Checks

For `2026 1.03`, `2026 1.04`, `2026 2.04`, `2026 2.08`, and `2026 5.04`:

- Open `Pick Decision Lab`.
- Verify the top cards show the pick label, pick value, score source, score
  column, score lineage, formula version, tier, top rookie cluster, nearby model
  neighbors, trade reality, guardrail, and human question.
- Verify `2026 1.03` and `2026 1.04` show early-first pick context with
  guardrails such as `internal_model_neighbor_only_not_one_for_one_trade_equivalent`.
- Verify `2026 2.04` and `2026 2.08` show second-round context with nearby
  model-value guardrails, not one-for-one trade equivalence.
- Verify `2026 5.04` stays `Manual-only: no exact model baseline`, with blank
  or manual-only pick value where appropriate.
- Verify the selected-pick filter narrows the decision lab without changing
  values, warnings, or source disclosure.

Fail the smoke test if missing-baseline `2026 5.04` receives an invented score,
or if nearby model neighbors are described as market prices or automatic trade
equivalents.

## Rookie Analyzer Filter Checks

| Check | Steps | Expected Result |
|---|---|---|
| Draft Room Filters | Open `Draft Room Filters` | Pick, rookie position, board band, evidence status, NFL team, draft round, and warning filters are available where data exists |
| Rookie Position | Select `RB`, `WR`, `QB`, and `TE` one at a time | Rows narrow by position without changing score, trust cap, warning, or source values |
| Rookie board band | Select first-round, second-round, watchlist, and data-incomplete bands where available | Rows match selected bands and retain `review_only_no_final_rookie_pick_recommendation` warnings |
| Evidence status | Select `draftable_review`, `manual_scout_source_review`, and `watchlist_data_incomplete` where available | Trust level and warning groups remain visible |
| Warning Type | Select source-limited, manual-only, missing, or no-premium warnings where available | Rows carrying the selected warning stay visible with warning details |
| Clear filters | Restore defaults | Full rookie review row set returns |

## Rookie Row Traceability

| Prospect | Why To Check | Expected Smoke Result |
|---|---|---|
| Jeremiyah Love | Top rookie board anchor and owned-pick candidate | `league_format_adjusted_score` source stays visible; source-limited/current-college warnings remain review-only |
| Makai Lemon | Top WR rookie and 2.04 neighborhood row | Source disclosure and warning groups remain visible |
| Skyler Bell | Model-separation warning row | `Model Separation / Source Warning` is visible as review context, not a draft instruction |
| Jordyn Tyson | Top-cluster row with adjusted format score | Raw/format distinction remains visible where shown |
| Carnell Tate | Top-cluster rookie/current bridge row | Warning details remain visible |
| Antonio Williams | 2.04 candidate context | Candidate-cluster context does not become a final pick call |
| Daniel Sobkowicz | Mandatory low-evidence watchlist anchor | `watchlist_data_incomplete` and missing-evidence warnings remain visible; row does not masquerade as confident |
| Eli Raridon | 5.04 late-watchlist candidate | No exact pick baseline is invented for 5.04 context |
| Kadarius Calloway | 5.04 late-watchlist candidate | No exact pick baseline is invented for 5.04 context |

## Rookie Board Tabs And Drilldown

- Open the rookie board subtabs and confirm `Review Order`, `Player`, `Final
  Score`, `Trust Cap`, `Trust Level`, `Board Band`, `Warning Groups`, `Warning
  Details`, and `Why This Review Order` are visible where expected.
- Open player drilldown via `Player Detail`.
- Confirm `Player Detail` repeats the selected prospect, position, team/college,
  model value, trust status, warning groups, and source pointer.
- Confirm `Why This Review Order` explains admitted evidence only and does not
  add market, ADP, rankings, projections, consensus, startup, or trade-calculator
  logic to private value.

## Receipts And Warnings Checks

| Surface | Smoke Check |
|---|---|
| `Receipts / Warnings` | Receipts, components, and warnings tabs are visible and tied to the filtered rookie/pick context |
| `Receipts` | Receipt rows include prospect/pick identity, component or source context, raw values, contribution/evidence fields, and warning text where available |
| `Components` | Component rows explain model shape without changing scores |
| `Warnings` | Warning rows expose manual-review and blocked-use context |
| `Advanced: current option receipts` | Current live-draft option receipts are visible for inspection only |
| `Advanced: state and source details` | Source readiness details are visible without changing active state |

Fail the smoke test if receipt expanders are hidden from the review path, or if
warnings are replaced by final recommendations.

## Live Draft Controls: Observe-Only Pass

The bottom Draft Room sections are stateful. For this R19 smoke checklist,
verify visibility only:

- `Best Options Right Now`
- `Pick Grid`
- `Search / Assign`
- `Best Remaining By Position`
- `Recent Picks`
- `Drafted Picks`
- `Draft Backups`
- `Mock Save / Load`
- `My Picks`
- `Advanced: state and source details`

Do not use stateful buttons during this checklist unless you are deliberately
testing a disposable mock draft and have recorded that the test state is safe to
discard.

## Market And Context Guardrails

- Market, research, startup, historical comps, and model-neighborhood context
  may appear as display or review context only.
- Market or research context must not populate rookie `Final Score`.
- Startup/internal neighbors must not be presented as one-for-one trade prices.
- Review labels such as `review_defer_context`,
  `review_rookie_vs_veteran`, and `manual_only_no_exact_model_baseline` must
  remain prompts for human judgment, not final actions.
- Pick and rookie blocked-use fields must remain aligned with:
  `do_not_use_as_final_rookie_draft_recommendation`,
  `do_not_use_as_pick_trade_recommendation_or_offer`, or
  `do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation`.

## Fail Conditions

Stop and document a bug if any of these are observed:

- A Draft Room filter/search action mutates draft state or generated outputs.
- `2026 5.04` receives an exact pick baseline where the audit says none exists.
- Candidate clusters or nearby model neighbors are shown as final draft picks,
  final trade offers, or market prices.
- Rookie warnings are hidden, removed, or replaced by recommendation text.
- Receipts/components/warnings cannot be reached from the review path.
- Market, ADP, ranking, projection, consensus, startup, or trade-calculator
  context drives rookie private value.
- The page encourages final trade, cut, keep, draft, buy, sell, defer, target,
  or start/sit decisions without human review.

## Evidence Capture Worksheet

| Field | Tester Entry |
|---|---|
| Date/time |  |
| App URL |  |
| Active pack caption |  |
| Browser |  |
| Draft Room loaded | Pass / Fail |
| Stateful controls avoided | Pass / Fail |
| Owned Pick Decision Lab pass | Pass / Fail |
| `2026 5.04` manual-only pass | Pass / Fail |
| Rookie filters pass | Pass / Fail |
| Rookie row traceability pass | Pass / Fail |
| Receipts visible | Pass / Fail |
| Warning groups visible | Pass / Fail |
| Market/context guardrails pass | Pass / Fail |
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
  is a UX/source-disclosure smoke test only.
