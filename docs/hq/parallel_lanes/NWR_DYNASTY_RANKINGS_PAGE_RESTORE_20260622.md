# NWR Dynasty Rankings Page Restore - 2026-06-22

## Verdict

GREEN.

The Streamlit `/rankings` route now opens a split page where the first tab is the
approved full Dynasty Rankings view and the second tab is the frozen Final Draft
Board V1 view.

This is a page/source-routing repair only. No rankings were generated, no model
scores were recalculated, no `latest_candidate` or `latest_approved` pointers
were changed, and the pinned snapshot was not mutated.

## Root Cause

The draft-day app compression had routed the visible Dynasty Rankings / Final
Board page directly to the frozen 66-row Final Draft Board V1. That made the
Dynasty Rankings surface look like a rookie/draft-board-only page instead of the
previous full dynasty rankings page.

## Correct Full Dynasty Source

Approved source restored locally:

`local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`

Observed source hash:

`263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`

Supporting repo policy/evidence:

- `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md`
- `docs/model_v4/RANKINGS_POST_PATCH_ACCEPTANCE_AUDIT_20260609.md`
- `docs/model_v4/POST_RANKINGS_DRAFT_LIVE_DETAIL_CHECKPOINT_20260609.md`

The local artifact has 240 rows:

| Metric | Count |
| --- | ---: |
| Dynasty rows | 240 |
| QB/RB/WR/TE rows | 232 |
| K rows | 8 |
| NWR scored rows | 232 |
| Veteran/current-player rows by source flag | 240 |
| Rookie-flagged rows by source flag | 0 |

The source is a current-player dynasty rankings board. It contains veteran names
such as Puka Nacua, Bijan Robinson, Josh Allen, Patrick Mahomes, and Lamar
Jackson. It does not mark rows as rookies via `is_rookie`; rookie draft-board
rows remain in the frozen draft board/export lane.

## Page Behavior

`/rankings` now displays:

1. `Dynasty Rankings (Full)`: approved 240-row full dynasty rankings artifact.
2. `Final Draft Board (Frozen 66)`: frozen Final Draft Board V1 for draft-day
   board/live draft workflows.

Display rules:

- Market Rank and League Rank are labeled display-only.
- Technical source/bookkeeping columns are not displayed.
- Hidden sort/private-value fields are not created.
- User table sorting remains visible/user-controlled through Streamlit.
- The full dynasty source does not overwrite `final_board_rank`.

## Frozen Board Status

Frozen Final Draft Board V1 remains unchanged and loaded from the existing
frozen board path. Row count remains 66.

The Live Draft Room and other draft-day lane pages still use the frozen 66-row
board, not the full dynasty rankings artifact.

## Validation

- Focused pytest: `37 passed`.
- Ruff on touched files: passed.
- PowerShell start script syntax: passed.
- Streamlit start script: started local app on `http://127.0.0.1:8501/rankings`.
- Browser smoke:
  - `/rankings` loads with approved full Dynasty Rankings, 240 rows, no traceback.
  - `/rankings` direct URL no longer shows Streamlit page-not-found after restart.
  - Fresh Live Draft Room check loaded frozen 66-row source and no page-not-found.
- Local service check:
  - Dynasty rows: 240.
  - Frozen board rows: 66.
  - Dynasty source hash matched expected.

## Guardrails

- No tuning was rerun.
- No rankings were regenerated.
- No `latest_candidate` or `latest_approved` pointer was updated.
- Pinned snapshot hash remained unchanged.
- No Mock Draft simulator logic was changed.
- No `C:\NWR_SHARED_DATA` files were tracked.
- No raw vendor CSVs or raw prediction dumps were added.
- Local restored full-board CSV remains under ignored `local_exports/` and is not
  committed.
