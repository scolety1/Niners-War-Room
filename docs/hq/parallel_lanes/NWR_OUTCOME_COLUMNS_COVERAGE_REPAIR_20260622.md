# Outcome Columns Coverage Repair - 2026-06-22

## Scope

Lane: Outcome Columns

Repo: `C:\NWR\Niners-War-Room`

Branch: `work/hq-parallel-control`

Starting HEAD: `aaf1923e0ac9addadf902d09dd42375391b4845e`

Purpose: trace the Outcome Columns app prop YELLOW-HOLD, determine whether 12 matched / 54 unmatched was a repairable wiring issue, and repair only safe display/status behavior without changing Outcome model logic, Outcome display contract, final board ranking, pinned snapshots, or shared exchange state.

## Source Trace

Frozen board loaded by the app:

`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`

Board row count: 66

Outcome Columns app prop loaded by the app:

`C:\NWR_SHARED_DATA\draft_day_app_props\20260622\outcome_columns\outcome_player_context.csv`

Repo fallback Outcome Columns prop:

`C:\NWR\Niners-War-Room\docs\draft_day_exports\final_board_v1_20260622\app_props\outcome_columns\outcome_player_context.csv`

Approved Outcome V1 numeric display artifact:

`C:\NWR\Niners-War-Room-outcome\app\generated\outcome_probability\numeric_outcome_display_v1.csv`

Outcome V1 closeout documentation confirms the approved display heads are limited to:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

No Top 6 heads, hidden sort keys, ranking/sorting effects, or promoted artifacts were used.

## Coverage Finding

Before repair:

- Context rows: 66
- Matched rows: 12
- Unmatched rows: 54
- Status: YELLOW-HOLD

After repair:

- Context rows: 66
- Matched rows: 12
- Unmatched rows: 54
- Status: YELLOW-HOLD

The 54 unmatched rows are not caused by a bad app join, stale fallback-only behavior, player_id mismatch, name normalization issue, or position filter issue. They are caused by approved source coverage: the frozen final board includes many rookie/prospect rows that are not present in the approved Outcome V1 numeric display artifact.

The approved Outcome V1 artifact contains 240 rows, including 227 available rows, but it does not contain names for 54 of the 66 frozen final board rows. A loose normalized name check also fails for those 54 rows. Because the approved source does not contain safe display-only values for them, Outcome values cannot be backfilled without fabricating values or rerunning/changing the model, both of which are blocked by the lane guardrails.

Full matched/unmatched table:

`C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_OUTCOME_COLUMNS_COVERAGE_MATCH_TABLE_20260622.csv`

## Root Cause

Root cause: approved Outcome source coverage is a subset of the frozen board, not an app wiring failure.

Specific cause classification:

- Missing approved Outcome data: yes, for 54 board rows.
- Wrong source file: no.
- Stale fallback file: fallback was incomplete as a status package, but not the cause of 12/54 coverage.
- Bad join key: no.
- player_id mismatch: not applicable for the frozen board, which does not expose player_id.
- Name normalization issue: no.
- Position filter issue: no.
- Source artifact only covering subset: yes.

## Safe Repairs Made

- Outcome Columns page now displays context, matched, and unmatched counts from `match_status`.
- Outcome Columns page now surfaces a YELLOW-HOLD message directly on the page when coverage is partial.
- Repo-contained fallback Outcome app props now include status, display rules, and manifest files so fallback mode remains truthful.
- Tests now cover Outcome match count behavior and repo fallback YELLOW-HOLD status.

No shared-data props were changed. No latest_candidate/latest_approved files were changed. No pinned snapshot was changed. No Outcome model logic, columns, rank behavior, sorting behavior, or final board rows were changed.

## Human Decision Needed

No engineering repair can safely turn this GREEN from the current approved source. A human lane decision is needed if draft-day Outcome coverage should become complete:

- approve leaving Outcome Columns as partial display-only YELLOW-HOLD context, or
- explicitly authorize a future Outcome lane model/data refresh that covers the frozen board players, then re-approve the resulting display artifact.

## Validation

- Focused pytest: PASS
  - `python -m pytest tests\test_draft_day_app_v1_service.py`
  - Result: 12 passed
- Ruff on touched Python files: PASS
  - `python -m ruff check app\pages\26_outcome_columns_v1.py src\services\draft_day_app_v1_service.py tests\test_draft_day_app_v1_service.py`
- Git diff check: PASS
  - `git diff --check`
- Streamlit start script: PASS
  - `scripts\start_draft_day_app.ps1 -Port 8501`
  - `/rankings` returned HTTP 200
- Browser smoke: PASS
  - Live Draft Room
  - Final Board / Dynasty Rankings
  - Player Compare
  - Trading Lab
  - Mock Draft
  - Draft Prep
  - Outcome Columns
  - Decision Board
  - Settings / Data Health
- Outcome Columns page status: PASS
  - Page displays `12 matched / 54 unmatched`
  - Page remains YELLOW-HOLD
- Frozen board row count: PASS
  - 66 rows
- Pinned manifest hash: PASS
  - `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- latest_candidate/latest_approved: PASS
  - No Outcome lane exchange latest pointer files were created or updated by this task.
- Changed-file scope: PASS
  - No `C:\NWR_SHARED_DATA` files were tracked.
  - No raw vendor CSVs or raw prediction dumps were added.
  - No Mock Draft simulator logic changed.

## Verdict

YELLOW-HOLD. The app is safer and clearer, but Outcome Columns coverage remains partial because the approved source does not contain 54 frozen-board players.
