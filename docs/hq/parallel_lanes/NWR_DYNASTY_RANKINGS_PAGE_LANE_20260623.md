# NWR Dynasty Rankings Page Lane - 2026-06-23

## Final Verdict

GREEN with known data caveat: `/rankings` is usable as the normal NWR Dynasty Rankings player board. The approved full dynasty source currently contains 240 supported rows, all marked non-rookie/non-prospect, so rookie/prospect filtering is present but has no source-backed full-dynasty rows to return.

## Source Used

- Source: `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`
- Source hash: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Row count: 240
- Veterans/non-rookies: 240
- Rookies/prospects: 0 in the approved full dynasty source
- Frozen Final Draft Board V1: 66 rows, unchanged
- Puka Nacua: NWR rank 1
- Zay Flowers: NWR rank 12

## Default Page Behavior

Before:
- `/rankings` used the unified draft-day board surface and foregrounded draft/review clutter in the full dynasty table.
- Full Dynasty view could expose review-only candidate rank/value columns and allowed Final Board Rank as a full-view sort option.

After:
- Default view is `Full Dynasty Rankings`.
- Default sort is `Dynasty Rank` ascending.
- Default position filter is `QB`, `RB`, `WR`, `TE`; kickers are hidden by default.
- Default table is the NWR dynasty board, with draft-board and unified-review fields kept out of the default table.
- Optional Draft Board / Unified Review views still retain draft-board context.

## Visible Default Columns

- Dynasty Rank
- Player
- Pos
- NFL Team
- Age
- Position Rank
- Candidate Band
- NWR Dynasty Score
- Trust
- Confidence
- Position-applicable outcome display columns
- Key Caveat / Review Flag

Not foregrounded by default:
- Final Board Rank
- Final Tier
- Source Coverage
- Asset Type
- Board Availability
- Draft Action
- ADP / market / DynastyProcess
- Raw technical/source columns
- Hidden sort fields

## Filters Added / Verified

- Search player
- Position multi-select: QB, RB, WR, TE
- Player type: All, Rookies / prospects, Veterans, Full Dynasty source
- Team filter
- Age range
- Tier / band
- Outcome availability
- Confidence
- Manual review
- Sort by Dynasty Rank, Position Rank, Age, Player in full view
- Candidate Rank sort remains review-only in Unified Review only

## Browser Proof

Local Streamlit URL used: `http://127.0.0.1:8502`

- `/rankings` opened with no page-not-found dialog and no traceback.
- Main ranking table appeared near the top.
- Default view: `Full Dynasty Rankings`.
- Default row count: 216 shown after default no-kicker QB/RB/WR/TE filter.
- Compact source badges showed full dynasty rows 240, veterans 240, rookies/prospects 0, frozen board rows 66.
- Default order was Dynasty Rank ascending; visible top rows showed Puka Nacua rank 1 above the rest of the board.
- Zay Flowers search produced a one-row result at Dynasty Rank 12.
- WR position filter produced 86 rows and WR-only outcome heads.
- TE position filter produced 30 rows and TE-only outcome head.
- No kickers appeared by default.
- No Final Board Rank, Source Coverage, Asset Type, Draft Action, or Candidate Rank columns appeared in the default table.
- Smoke checks passed with no page-not-found and no traceback:
  - `/live-draft-room`
  - `/player-compare`
  - `/mock-draft`
  - `/trading-lab`

## Remaining Caveats

- The current approved full dynasty source does not include rookie/prospect rows. The page does not fabricate rookie dynasty rows from the frozen draft board.
- Position Rank in the full dynasty view is derived in-memory from approved NWR overall rank and position for display/sort only; no source rank files are changed.
- Outcome columns remain display-only. Same-position missing values and missing display facts are rendered as `Not enough information` by the display service.

## Guardrail Confirmations

- Frozen Final Draft Board V1 was not mutated and remains 66 rows.
- `final_board_rank` was not changed.
- Approved Dynasty Rank / NWR Rank was not overwritten.
- `latest_candidate` was not updated.
- `latest_approved` was not updated.
- Pinned snapshot was not mutated; pinned manifest hash remained `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- No `C:\NWR_SHARED_DATA` files were tracked.
- No raw vendor CSVs or prediction dumps were added.
- No model, value, rank, or source-truth artifacts were mutated.
- DynastyProcess / market baseline data was not wired into app pages, model logic, sorting, ranks, or values.
- No hosted deployment and no push.

## Validation

- Focused pytest: `44 passed`
- Ruff on touched files: passed
- Python compile checks on touched Python files: passed
- `git diff --check`: passed
- Browser proof completed through local Streamlit
