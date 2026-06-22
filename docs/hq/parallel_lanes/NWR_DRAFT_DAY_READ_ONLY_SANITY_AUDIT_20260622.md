# NWR Draft-Day Read-Only Sanity Audit - 2026-06-22

Verdict: YELLOW

This was a read-only draft-day sanity audit of the current frozen board, full dynasty rankings source, and draft-day lane props while app workflow lanes continue in parallel. No source data, model code, app code, rankings, frozen board files, `latest_candidate`, `latest_approved`, or pinned snapshot files were changed.

YELLOW means the frozen board is coherent enough to remain the draft-day source of truth, but several data/workflow issues could embarrass the room if the app does not label them clearly.

## Sources Checked

| Source | Path | Rows | Notes |
|---|---:|---:|---|
| Frozen Final Draft Board V1 | `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv` | 66 | Draft-day source of truth |
| Full Dynasty Rankings | `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv` | 240 | Broad veteran/current player universe |
| Outcome props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\outcome_columns\outcome_player_context.csv` | 66 | 12 players with matched probability context |
| Trading Lab props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\trading_lab\trade_helper_context.csv` | 66 | Row-level match to frozen board |
| Decision Board props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\decision_board\decision_flags_context.csv` | 66 | Row-level match to frozen board |
| Mock Draft availability props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\mock_draft\availability_context.csv` | 89 | Includes frozen-board rows plus extra context |
| Rookie overlay | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\rookie_hq\rookie_overlay_context.csv` | 54 | Covers rookie/prospect board rows only |

## Board Sanity

Frozen board row count is 66. Position coverage is:

| Position | Rows |
|---|---:|
| WR | 38 |
| RB | 22 |
| QB | 3 |
| TE | 3 |

The visible `final_board_rank` is contiguous from 1 to 66. No duplicate player/position rows were found in the frozen board.

The frozen board does not include a `player_id` column. Most app prop files also do not include `player_id`, so current cross-lane joins rely mostly on normalized player name, position, rank keys, and lane-specific context. That is usable for tomorrow, but it is a real future maintenance risk.

## Dynasty Rankings

The full Dynasty Rankings source exists and has 240 rows. It is not rookie-only; it contains a broad veteran/current-player universe. However, it does not cover the 54 rookie/prospect rows in the frozen board by name/position, and its `is_rookie` flag is `0` for all 240 rows.

This means the Dynasty page must be labeled carefully:

- Full Dynasty Rankings: 240-row legacy/current-player dynasty source.
- Frozen Final Draft Board V1: 66-row draft-day source of truth.
- Do not imply the Dynasty source fully covers the frozen rookie/prospect draft pool.

## Cross-Source Joins

Frozen board row-level match results:

| Source | Matched Frozen Rows | Missing Frozen Rows | Notes |
|---|---:|---:|---|
| Full Dynasty Rankings | 12 | 54 | Only dropped/current-player overlap matched |
| Outcome props | 66 | 0 | Prop rows exist for all board rows |
| Outcome probabilities | 12 | 54 | Only 12 have matched probability context |
| Trading Lab props | 66 | 0 | Row-level context matched |
| Decision Board props | 66 | 0 | Row-level context matched |
| Mock Draft availability | 66 | 0 | Row-level context matched |
| Rookie overlay | 54 | 12 | Expected: dropped veterans are not in rookie overlay |
| Manual cards | 36 | 30 | Expected: cards exist only for manual-review rows |

Highest-risk missing Dynasty overlaps from the frozen top ranks include Jeremiyah Love, Makai Lemon, Carnell Tate, KC Concepcion, Jadarian Price, Denzel Boston, Germie Bernard, Chris Bell, Zachariah Branch, and Antonio Williams.

## Outcome Sanity

Outcome coverage is partial:

- 12 of 66 frozen-board players have matched Outcome probability context.
- 54 of 66 are `unmatched_no_outcome_row`.
- The Outcome prop file stores blanks for missing probability values, not the literal text `Not enough information`.

The app must convert missing Outcome values to exactly `Not enough information` in user-facing rankings/player views. Blank cells are a draft-day UX failure.

## Availability And Label Risks

Ten frozen-board rows have team labels needing review:

| Rank | Player | Pos | Team |
|---:|---|---|---|
| 27 | Sieh Bangura | RB | needs_data |
| 32 | Jacob De Jesus | WR | needs_data |
| 36 | Devin Voisin | WR | needs_data |
| 38 | O'Mega Blake | WR | needs_data |
| 44 | Barika Kpeenu | RB | needs_data |
| 52 | Braylon James | WR | needs_data |
| 59 | Jamarion Miller | RB | needs_data |
| 61 | Chip Trayanum | RB | needs_data |
| 64 | Keenan Allen | WR | UNKNOWN |
| 66 | Darren Waller | TE | UNKNOWN |

These should be visible manual-review caveats, not silently hidden.

## Manual Review Flags

The frozen package has 36 manual-review rows. The most important top-board examples:

| Rank | Player | Pos | Primary Review Reason |
|---:|---|---|---|
| 10 | Antonio Williams | WR | Critical trap guard |
| 11 | Jonah Coleman | RB | Feature-driven rank move requires role confirmation |
| 12 | Skyler Bell | WR | Target-earning path question |
| 13 | Brenen Thompson | WR | Target-earning path question |
| 14 | Elijah Sarratt | WR | Target-earning path question |
| 15 | Emmett Johnson | RB | Early-down/goal-line role question |
| 16 | Kaytron Allen | RB | Early-down/goal-line role question |
| 17 | Adam Randall | RB | Early-down/goal-line role question |
| 18 | Josh Cameron | WR | Target-earning path question |
| 19 | Nicholas Singleton | RB | Early-down/goal-line role question |

Fourteen high-score rows have caveats. The top of the board is usable, but should be reviewed as a human board, not treated as mechanically final advice.

## Display-Only And Guardrail Findings

No source/model/app files were changed in this audit.

Guardrail-sensitive columns found:

- `dynasty.market_rank`
- `dynasty.market_rank_source`
- `trading.display_only_adp_market_status`
- `trading.private_value_created`
- `trading.hidden_sort_field_created`

The Trading Lab `private_value_created` and `hidden_sort_field_created` columns appear to be explicit guardrail/status audit columns, not hidden sort fields. They should remain hidden from main user-facing tables or shown only in diagnostics.

Dynasty market-rank fields must remain display-only. They must not control model score, final board rank, hidden sort, draft advice, or private value.

## Stale Label Risks

Detected date/source markers:

- Frozen board references 2026-06-20 and 2026-06-21 context.
- Trading, Mock Draft, and manual card props reference 2026-06-20 context.
- Dynasty source includes a `FantasyPros February 27, 2026` marker in market/league-rank context.

No stale June 15 marker was identified in the checked data files, but UI labels should still avoid implying old market/rank context is a live source of truth.

## Ten Highest-Risk Draft-Day Data Issues

1. Outcome probability coverage is only 12 of 66 frozen-board players.
2. Missing Outcome values are blank in the prop file and must display as `Not enough information`.
3. Full Dynasty Rankings does not cover the 54 frozen rookie/prospect rows.
4. Dynasty `is_rookie` is `0` for all 240 rows, so it is not a reliable rookie indicator.
5. Frozen board and most app props lack `player_id`, making joins name/rank dependent.
6. Ten board rows have `needs_data` or `UNKNOWN` team labels.
7. Thirty-six rows require manual review, including many top-20 names.
8. Fourteen high-score rows carry role/target/trap caveats.
9. Market/rank context exists in Dynasty props and must stay display-only.
10. Technical guardrail columns in Trading Lab props could embarrass the workflow if surfaced in the main UI.

## Ten Most Useful Quick Fixes

Do not implement these from this audit lane unless separately approved:

1. Verify every missing Outcome probability renders exactly as `Not enough information`.
2. Keep visible source badges and row counts on Final Board, Dynasty Rankings, Outcome, Trading, Mock Draft, and Draft Prep pages.
3. Hide technical bookkeeping columns from all main user-facing tables.
4. Add a clear Dynasty note: 240-row legacy/current-player source, not the frozen 66-row draft board.
5. Add a visible filter/list for the ten `needs_data` or `UNKNOWN` team rows.
6. Prioritize human review for the 14 high-score caveat rows.
7. Keep Outcome as YELLOW-HOLD/PARTIAL unless a candidate refresh is separately approved.
8. Add a future player-ID bridge across frozen board and prop artifacts.
9. Re-smoke the app after all workflow lanes merge, using browser proof rather than render-only tests.
10. Keep ADP, market, projections, rankings, vendor, and trade-calculator context display-only.

## Human Decisions Needed

1. Accept partial Outcome coverage for tomorrow, or hide Outcome except where supported.
2. Decide whether `needs_data` and `UNKNOWN` team labels are acceptable with manual-review warnings.
3. Decide how prominently to surface the top-board role/target caveats.
4. Decide whether the Dynasty page should be titled as a legacy/full-dynasty reference separate from the frozen draft board.
5. Decide whether a future, post-draft player-ID normalization package is required.

## Audit Closure

Final verdict: YELLOW.

The frozen 66-player board is structurally coherent and should remain the source of truth. The embarrassing risks are not duplicate ranks or raw board corruption; they are partial Outcome coverage, weak ID joins, stale/display-only context clarity, team-label gaps, and manual-review caveats that must be visible in the app.

No app code, model code, ranking logic, frozen-board data, pinned snapshot, `latest_candidate`, or `latest_approved` files were changed.
