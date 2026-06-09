# Player Board UX Smoke Checklist

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: provide a manual smoke-test checklist for the Player Board before any
formula work. This checklist verifies filters, score disclosure, warnings, and
named-player traceability. It does not tune formulas, change generated outputs,
or make trade, cut, keep, draft, buy, sell, defer, target, or start/sit
recommendations.

## Evidence Sources

- Player Board UI: `app/pages/05_rankings.py`
- Score resolver: `src/services/player_board_score_service.py`
- Shared score envelope: `src/services/review_score_envelope_service.py`
- Primary current-player source:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Primary score column: `checkpoint_review_score`
- Legacy comparison source: active-pack `private_score`, exposed only as
  `legacy_active_pack_score`
- Existing source-routing tests: `tests/test_player_board_score_service.py`
- Supporting reports:
  `docs/model_v4/CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md` and
  `docs/model_v4/LEGACY_VS_CURRENT_SENTINEL_EXPANSION_20260605.md`

## Setup

1. Launch the app using the normal local Streamlit workflow.
2. Open `Player Board`.
3. Record the active pack caption, timestamp, browser, and tester initials.
4. Start with default filters and no search text.
5. Keep this pass manual and observational. Do not edit active rankings, My
   Team, War Board, readiness gates, active data packs, generated outputs, or
   user-entered draft state.

## Primary Score Disclosure

For several visible rows and every named-player trace below, verify:

- The main board labels the primary value as `Model v4 Current Value`.
- `Score Source File` points to the current-player checkpoint path, not an
  active-pack score file.
- `Score Column` is `checkpoint_review_score`.
- `Score Lineage` is `review_v4_current_player` or a clear current-player
  review lineage.
- `Model Version`, `Trust Cap`, `Source Status`, and `Warnings` are visible in
  the table, detail panel, raw fields, or source-disclosure columns.
- Rows without a valid current-player checkpoint score fail closed instead of
  using legacy, market, ADP, ranking, projection, startup, or consensus context
  as primary value.

Fail the smoke test if `private_score`, `legacy_active_pack_score`, league rank,
ADP, projection, consensus, startup, market gap, or trade-calculator context is
shown or sorted as the primary Player Board model value.

## Filter And Search Checks

| Check | Steps | Expected Result |
|---|---|---|
| Default board | Open Player Board with no search text | Rows load, default columns include model value, source file, score column, lineage, trust, and warning group |
| Position filter | Open `Advanced Filters`, choose only `WR`, then only `RB`, then only `QB`, then only `TE` | Rows are constrained to the selected position without changing scores or source disclosure |
| Owner filter | Select one owner from `Owner` | Rows are constrained to the selected owner and still show source disclosure |
| Min Model Value | Move `Min Model Value` upward, then reset to `0` | Low-value and blank-score rows are hidden by the threshold, then restored after reset |
| Audit-watch warnings | Turn on `Show audit-watch warnings only` | Rows all carry route, age, TE, first-down, or missingness warning text |
| Search by player | Search `Keenan Allen`, `Darius Slayton`, `Trey McBride`, `Josh Allen`, `De'Von Achane`, `Kaleb Johnson`, and `Luke McCaffrey` | Exact or expected matching rows appear; source disclosure remains visible |
| Search by team/position/owner | Search a known visible team, position, or owner value | Search narrows rows without changing values |
| Clear filters | Clear search, restore all positions and owners, reset min value, disable warning-only | Board returns to the default row set |

## Detail Panel Checks

For three rows from different positions:

- Use `Inspect player` and open the detail panel.
- Confirm the detail panel repeats the selected player, position, team, owner,
  model value, rank/order, trust status, warning groups, market context marked
  display-only, and source pointer.
- Confirm language remains review-only. It may explain keep priority, drop
  pressure, or trade context, but it must not issue final trade, cut, keep,
  draft, buy, sell, defer, target, or start/sit instructions.
- Confirm market context says display-only and does not replace the primary
  model value.

## Source And Warning Expanders

| Expander | Smoke Check |
|---|---|
| How to read this page | Explains `Model Value`, source file, source column, model version, score lineage, trust cap, warnings, and market context as read-only |
| Market Context (Read-Only) | League rank, startup ADP, and market-gap columns are hidden by default and described as display-only |
| Formula Components | Component columns appear as explanatory context and do not replace primary value |
| Advanced: raw formula fields | Raw fields include source disclosure and comparison-only legacy columns where available |
| Audit Watchlist | Warning-only rows expose route, age, TE, first-down, or missingness flags |
| TE No-Premium Review | TE rows stay framed in no-premium context, not TE-premium recommendations |

## Named-Player Traceability

| Player | Why To Check | Expected Smoke Result |
|---|---|---|
| Keenan Allen | Mandatory legacy sentinel | Current checkpoint score `41.6097` is primary where present; legacy active-pack `82.4` is comparison-only and not sorted as primary |
| Darius Slayton | Mandatory legacy sentinel fail-closed case | Legacy active-pack `78.88` is not primary; if no Model v4 row exists, primary model value is blank/fail-closed with manual-review warning |
| Trey McBride | Highest extracted TE checkpoint row | Source disclosure remains current-player checkpoint; no-premium TE context is review-only |
| Josh Allen | 1QB QB context row | QB value is visible with format/risk context; no superflex or final trade-equivalence framing |
| De'Von Achane | High-value RB with source-gap review context | Warning groups are visible and review-only |
| Christian McCaffrey | Veteran RB age-window row | Age-warning context is visible; no age-curve formula implication |
| Jonathan Taylor | RB age-window comparison row | Age-window context is visible and does not change displayed score during the smoke pass |
| Malik Nabers | Young WR evidence review row | Young-player/source-gap warnings remain visible |
| Marvin Harrison Jr. | Young WR evidence review row | Source-gap warnings remain visible |
| Brian Thomas Jr. | Young WR evidence review row | Source-gap warnings remain visible |
| Kaleb Johnson | Low-value/source-gap row | Score and warnings are visible; row is not turned into a final roster or draft instruction |
| Luke McCaffrey | Roster-pressure/source-gap row | Warning text is visible; no final cut/drop instruction is issued |
| T.J. Hockenson | TE/veteran context spot check if present | TE/no-premium or status context remains review-only |

## Sorting And Blank-Score Checks

- Verify the default `Review Order` and visible order are driven by the repaired
  Player Board rows, not legacy active-pack `private_score`.
- Sort by visible columns if the Streamlit grid allows it, then restore default
  state by refreshing the page or clearing grid sort state.
- Blank or fail-closed primary scores must not float to the top when sorting
  model value descending.
- Keenan Allen must not be ordered as if his primary value were `82.4`.
- Darius Slayton must not be ordered as if his primary value were `78.88`.

## Market Display-Only Checks

- Open `Market Context (Read-Only)`.
- Confirm league rank, ADP, normalized ADP, and market-gap columns are present
  only in that read-only context or raw fields.
- Confirm the copy says market context does not drive private Model Value,
  formulas, roster pressure, or draft decisions.
- Confirm market context does not populate `Model v4 Current Value`, `Score
  Column`, or `Score Lineage`.

## Fail Conditions

Stop and document a bug if any of these are observed:

- Keenan Allen legacy `82.4` appears as the primary Player Board model value.
- Darius Slayton legacy `78.88` appears as the primary Player Board model value.
- `private_score` from the active pack appears as a primary or default-sort
  value instead of comparison-only legacy context.
- A row with missing source path, missing score column, unknown lineage,
  market-only lineage, or legacy-only lineage still shows a primary model value.
- ADP, rankings, projections, consensus, startup, market, or trade-calculator
  context populates primary private value.
- Review labels are shown as final trade, cut, keep, draft, buy, sell, defer,
  target, or start/sit recommendations.
- A filter or search action mutates active rankings, My Team, War Board,
  readiness gates, active data packs, generated outputs, or user draft state.

## Evidence Capture Worksheet

| Field | Tester Entry |
|---|---|
| Date/time |  |
| App URL |  |
| Active pack caption |  |
| Browser |  |
| Player Board loaded | Pass / Fail |
| Source disclosure visible | Pass / Fail |
| Position filter pass | Pass / Fail |
| Owner filter pass | Pass / Fail |
| Search pass | Pass / Fail |
| Warning-only filter pass | Pass / Fail |
| Market read-only pass | Pass / Fail |
| Keenan Allen sentinel pass | Pass / Fail |
| Darius Slayton sentinel pass | Pass / Fail |
| Named-player traceability pass | Pass / Fail |
| No final recommendation language | Pass / Fail |
| Notes/screenshots |  |

## Non-Goals

- Do not tune formulas from this checklist.
- Do not change weights, age curves, rookie weights, pick baselines, VORP,
  replacement formulas, market-gap thresholds, confidence cap magnitudes, or
  startup-slot conversion.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not use this checklist as proof the model is ready for money decisions.
  It is a UX/source-disclosure smoke test only.
