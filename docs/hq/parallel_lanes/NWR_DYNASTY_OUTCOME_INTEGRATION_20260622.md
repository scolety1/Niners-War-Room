# Dynasty Rankings + Outcome Integration - 2026-06-22

## Scope

Repo: `C:\NWR\Niners-War-Room`

Branch: `work/hq-parallel-control`

Starting HEAD: `d63110be4c23f2305601e24aeef9ab212494faaa`

Preserved local commits:

- `aaf1923e0ac9addadf902d09dd42375391b4845e`
- `d63110be4c23f2305601e24aeef9ab212494faaa`

Guardrails honored: no push, no latest_candidate/latest_approved update, no pinned snapshot mutation, no frozen board mutation, no final_board_rank changes, no model rerun, no fabricated probabilities, no raw vendor or prediction dumps added, and no `C:\NWR_SHARED_DATA` files tracked.

## Root Cause

The committed draft-day rankings page had been wired to the frozen 66-row Final Draft Board V1 via `load_frozen_board()` and rendered that board as the main `/rankings` experience. That made the page look rookie/prospect-only and hid the prior full Dynasty Rankings experience.

## Full Dynasty Source

Approved full Dynasty Rankings source found:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Source hash:

`263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`

Rows: 240

Positions:

- WR: 93
- RB: 79
- TE: 32
- QB: 28
- K: 8

The source includes veterans/current players and young players such as Puka Nacua, Jaxon Smith-Njigba, Bijan Robinson, Ashton Jeanty, Tetairoa McMillan, Omarion Hampton, Cam Ward, Brock Bowers, Malik Nabers, and Jayden Daniels. The artifact's `is_rookie` field is not populated for a reliable rookie split; all 240 rows currently carry a false/zero rookie flag. The UI therefore keeps the default table on all rows and labels the source flag honestly.

## Outcome Source

Approved Outcome V1 numeric source found:

`C:\NWR\Niners-War-Room-outcome\app\generated\outcome_probability\numeric_outcome_display_v1.csv`

Source hash:

`1fb63fec25f7893ed09004830c7eb4e5ed32c6622c08876849fb61a2e4826cb0`

Rows: 240

Join key: `player_id`

Approved display heads:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

Blocked heads such as Top 6 were not used.

## Integration Behavior

Dynasty Rankings is now the visible main route at `/rankings`. The page renders one main Dynasty Rankings table from the approved 240-row full-player artifact.

Outcome probabilities are integrated into the Dynasty Rankings table as display-only columns. They do not create hidden sort fields, rank fields, final-board overrides, or model inputs.

Missing, unavailable, or position-non-applicable Outcome cells display exactly:

`Not enough information.`

Outcome row-level coverage:

- Dynasty rows: 240
- Outcome rows matched by `player_id`: 240
- Outcome available: 227
- Outcome not enough information/unavailable: 13

The frozen Final Draft Board remains available as the frozen 66-row tab/source for draft-day workflows and Live Draft Room.

The Outcome page has been deemphasized in navigation as Outcome Diagnostics and remains useful for status, coverage, source trace, and hold explanation.

## Validation

- Focused pytest: PASS
  - `python -m pytest tests\test_draft_day_app_v1_service.py tests\test_navigation_compression.py tests\test_birthday_demo_guardrails.py`
  - Result: 34 passed
- Ruff on touched Python files: PASS
  - `python -m ruff check app\pages\20_final_board_v1.py app\navigation.py src\services\draft_day_app_v1_service.py tests\test_draft_day_app_v1_service.py tests\test_navigation_compression.py tests\test_birthday_demo_guardrails.py`
- Git diff check: PASS
  - `git diff --check`
- Streamlit start script: PASS
  - `scripts\start_draft_day_app.ps1 -Port 8501`
  - `/rankings` returned HTTP 200
- Browser smoke: PASS
  - Live Draft Room
  - Dynasty Rankings
  - Player Compare
  - Trading Lab
  - Mock Draft
  - Draft Prep
  - Outcome Diagnostics
  - Decision Board
  - Settings / Data Health
- Dynasty-specific browser checks: PASS
  - 240-row Dynasty source visible
  - Veteran/current-player sample visible
  - Outcome probability sample visible
  - `Not enough information.` visible
- Frozen board workflow checks: PASS
  - 66-row frozen board still loaded
  - Live Draft Room and draft workflow pages still use frozen board source
- Guardrails: PASS
  - Pinned manifest hash unchanged: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
  - No hidden/private sort-like fields in the Dynasty source frame
  - No `latest_candidate` or `latest_approved` update performed
  - No `C:\NWR_SHARED_DATA` files tracked
  - No raw vendor CSVs or prediction dumps added

Note: unrelated local workflow/mock-draft changes were present in the worktree during validation and were not staged by this task.

## Verdict

YELLOW. The app-level Dynasty/Outcome integration is repaired and validated, but the approved full-player artifact's `is_rookie` flag is not populated for a reliable rookie/veteran split. No unapproved rookie classification was fabricated.
