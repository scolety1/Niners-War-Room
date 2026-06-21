# NWR Streamlit App User Concern Audit - 2026-06-22

## Scope

This audit reviewed Draft-Day Streamlit App V1 on `work/hq-parallel-control`
after the app was previously marked travel-ready. The pasted user request did
not include the specific concern text, screenshots, or tab names in the
placeholder section, so this pass focused on source tracing, page-by-page QA,
and likely user-facing data/UI concerns.

No model tuning, final-board mutation, latest pointer update, pinned snapshot
mutation, simulator logic change, vendor import, hosted deployment, or shared
data commit was performed.

## Baseline

- Repo: `C:\NWR\Niners-War-Room`
- Branch: `work/hq-parallel-control`
- Baseline HEAD: `db7628cfe599d02baec771c92331f7d8ec2634d9`
- Expected commit subject: `Make draft-day app travel-ready`
- Initial git status: clean
- Frozen board source:
  `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- Frozen board rows: 66
- Frozen board SHA256:
  `0D520523C3BE496FE4708A55ECFAC9FD18E47488A14FA229F87EFE35E42E888F`
- Pinned manifest SHA256:
  `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`

## Source Contracts Read

- `docs\hq\parallel_lanes\NWR_STREAMLIT_DRAFT_DAY_APP_V1_INTEGRATION_20260622.md`
- `docs\hq\parallel_lanes\NWR_STREAMLIT_DRAFT_DAY_APP_V1_CONTRACT_20260622.md`
- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\APP_PROP_CONTRACT.md`
- Repo fallback folder:
  `docs\draft_day_exports\final_board_v1_20260622`

The service fallback order remains:

1. `NWR_DRAFT_DAY_DATA_ROOT` / `NWR_DRAFT_DAY_APP_PROPS_ROOT`
2. `C:\NWR_SHARED_DATA`
3. repo-contained fallback files

## Page Audit Summary

| Page | Route | Primary sources | Result |
|---|---|---|---|
| Live Draft Room | `/live-draft-room` | frozen board, mock availability props | GREEN |
| Final Board / Dynasty Rankings | `/rankings` | frozen board | GREEN |
| Player Compare | `/player-compare` | frozen board plus selected lane props | GREEN after UI fix |
| Trading Lab | `/trading-lab` | frozen board, trading props | GREEN after UI fix |
| Mock Draft | `/mock-draft` | frozen board, mock props | GREEN |
| Draft Prep | `/draft-room` | frozen board, lane status rows | GREEN with Outcome YELLOW-HOLD shown |
| Outcome Columns | `/outcome-columns` | frozen board, outcome props | YELLOW-HOLD data coverage |
| Decision Board | `/decision-board` | frozen board, decision props | GREEN |
| Settings / Data Health | `/settings` | frozen board, prop inventory, pinned hash | GREEN with Outcome YELLOW-HOLD shown |

Every page showed the Frozen Final Draft Board V1 source badge after the final
scripted app start. Browser smoke found no Streamlit exception, no technical
trade guardrail column leakage, and a 66-row signal on all nine pages.

## Issues Fixed

### Lane status reflected file existence instead of status files

`lane_prop_status_rows()` previously marked a lane GREEN when the primary CSV
existed. That hid the current Outcome Columns `YELLOW-HOLD` status even though
`OUTCOME_APP_PROP_STATUS.md` reports partial coverage.

Fix:

- Added lane status markdown parsing in
  `src\services\draft_day_app_v1_service.py`.
- Supports direct `Status: ...`, `Verdict: ...`, and `## Verdict` heading
  formats.
- Outcome Columns now reports `YELLOW-HOLD` in Draft Prep and Settings / Data
  Health.

### Technical prop bookkeeping was visible in app tables

Trading Lab prop files include guardrail bookkeeping fields such as
`hidden_sort_field_created`, `private_value_created`, and
`final_board_rank_override_allowed`. These are not hidden sort fields in the
model sense, but they are confusing in draft-day UI and can look like leakage.

Fix:

- Added `display_lane_prop_frame()` to hide only those technical bookkeeping
  columns in visible prop tables.
- Applied it to Player Compare and Trading Lab.
- Kept visible context, caveats, tier movement notes, scarcity notes, and
  display-only labels.

## Remaining YELLOW Items

Outcome Columns remains YELLOW-HOLD as source data context, not as an app
runtime failure.

- Source file:
  `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\outcome_columns\outcome_player_context.csv`
- Rows: 66
- Matched by player+position fallback: 12
- Unmatched: 54
- Cause: the frozen board does not include `player_id`; the app-prop contract
  currently uses safe visible `player` + `position` joins.

This does not block use of the frozen final board tomorrow. It does mean Outcome
Columns should be treated as partial display-only context unless the Outcome
lane publishes a stronger board-keyed prop package later under explicit approval.

## Human Decisions Needed

- Decide whether partial Outcome Columns coverage is acceptable as
  YELLOW-HOLD display-only context tomorrow.
- Any request to change board ranks, player pool, model values, drop/keeper
  decisions, or Mock Draft simulator behavior still requires explicit human
  approval.

## Validation

- `scripts\start_draft_day_app.ps1 -Port 8501`: launched successfully when the
  existing Streamlit preview environment was placed on `PATH`.
- `/rankings`: HTTP 200.
- Browser smoke after scripted launch: all nine pages passed.
- Focused pytest:
  `python -m pytest tests\test_draft_day_app_v1_service.py` -> 10 passed.
- Focused Ruff:
  `python -m ruff check src\services\draft_day_app_v1_service.py app\pages\22_player_compare_v1.py app\pages\23_trading_lab_v1.py tests\test_draft_day_app_v1_service.py`
  -> passed.
- `git diff --check`: passed.
- Frozen board row count remains 66.
- Pinned manifest hash matches expected hash.
- No `C:\NWR_SHARED_DATA` files were added to Git.
- No raw vendor CSVs or raw prediction dumps were added.
- No Mock Draft simulator logic was changed.

## Verdict

YELLOW. The app is safe to use tomorrow as the frozen-board source of truth, and
the user-facing UI/wiring issues found in this audit were fixed. The remaining
YELLOW item is Outcome Columns source coverage, which is display-only and does
not override the frozen board.
