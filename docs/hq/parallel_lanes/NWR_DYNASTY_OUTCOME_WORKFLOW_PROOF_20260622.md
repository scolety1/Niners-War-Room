# Dynasty Rankings + Outcome Player Board Proof/Repair - 2026-06-22

Lane: dynasty-outcome-player-board
Worktree: `C:\NWR\Niners-War-Room-dynasty-outcome-player-board`
Branch: `codex/dynasty-outcome-player-board-20260622`
Starting commit: `cc49fa6a30197b4b39e260031fc59c16ed51b36d`

## Verdict

GREEN.

Dynasty Rankings is usable for draft-day review. It is no longer a rookie-only or split-table experience. The page now presents one primary player board with explicit view modes:

- `Unified Review View`
- `Full Dynasty source`
- `Frozen Draft Board`

## Sources

Full dynasty source:

- Path: `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`
- Rows: 240
- SHA256: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Lane note: the dedicated worktree does not contain local-only `local_exports`, so the app reads the approved control-repo local artifact without copying or tracking it.

Frozen board source:

- Path: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- Rows: 66
- Status: unchanged

Outcome source:

- Path: `C:\NWR\Niners-War-Room-outcome\app\generated\outcome_probability\numeric_outcome_display_v1.csv`
- Rows: 240
- SHA256: `1fb63fec25f7893ed09004830c7eb4e5ed32c6622c08876849fb61a2e4826cb0`
- Usage: display-only

## Coverage

Unified player board rows: 294

- Full Dynasty source only: 228
- Full Dynasty source + Frozen Board: 12
- Frozen Draft Board only: 54

Outcome coverage:

- Unified player board Outcome available: 227 / 294
- Unified player board not enough information: 67 / 294
- Frozen-board Outcome support: 12 / 66
- Frozen-board unsupported: 54 / 66

Missing values display exactly as `Not enough information`. Frozen-board-only dynasty context displays as `Draft-board only` or `Not enough information`.

## Root Cause

The lane worktree did not contain the local-only full dynasty artifact under its own `local_exports` path. In addition, the frozen board has no `player_id`, so a strict player_id join could not identify the known 12-player overlap between the frozen board and the approved dynasty/Outcome sources.

The repair uses the existing approved sources only:

- Full dynasty source fallback reads the approved local artifact from the clean control repo.
- Frozen board joins use `player_id` when present and normalized `player name + position` when player_id is absent.
- Frozen-board-only rows are not assigned fabricated dynasty ranks, scores, or Outcome values.

## Browser Proof

URL checked: `http://127.0.0.1:8501/rankings`

Visible proof:

- Page title: `Dynasty Rankings / Player Board`
- Source badge: approved full Dynasty Rankings, 240 rows
- Source-of-truth badge: Frozen Final Draft Board V1, 66 rows
- Unified rows shown: 294
- Full Dynasty source view rows shown: 240
- Frozen Draft Board view rows shown: 66
- Veteran proof row: `Christian McCaffrey (RB, Full Dynasty source)`
- Frozen-board rookie/prospect proof row: `Jeremiyah Love (RB, Frozen Draft Board only, Final Board Rank 1)`
- Outcome display sample: `Zay Flowers WR T12 29%`
- Outcome support badge: `12 / 66`
- Missing Outcome/context text: `Not enough information`
- Display-only label: `Outcome Display-Only columns are display-only context`
- Internal leak check: no `player_id`, `hidden_sort`, `sort_key`, or `private_value` text visible in unified, frozen, or dynasty views.

Nine-page smoke:

- `/rankings`: rendered, no exception
- `/live_draft_room_v1`: rendered, no exception
- `/player_compare_v1`: rendered, no exception
- `/trading_lab_v1`: rendered, no exception
- `/mock_draft_v1`: rendered, no exception
- `/draft_prep_v1`: rendered, no exception
- `/outcome_columns_v1`: rendered, no exception
- `/decision_board_v1`: rendered, no exception
- `/settings_data_health_v1`: rendered, no exception

## Guardrails

- Frozen Final Draft Board V1 row count remains 66.
- Pinned snapshot hash unchanged: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- `latest_candidate.json`: not created by this lane.
- `latest_approved.json`: not created by this lane.
- No `C:\NWR_SHARED_DATA` files tracked.
- No raw vendor CSVs or raw prediction dumps added.
- No hidden sort fields added.
- No final_board_rank changes.
- No model, value, ranking, simulator, or Outcome probability logic changes.

## Validation

- `python -m pytest tests\test_draft_day_app_v1_service.py tests\test_birthday_demo_guardrails.py tests\test_navigation_compression.py tests\test_draft_day_workflow_service.py` - 42 passed.
- `python -m pytest tests\test_draft_day_app_v1_service.py tests\test_navigation_compression.py` - 28 passed after final wording/display patch.
- `python -m ruff check app\pages\20_final_board_v1.py src\services\draft_day_app_v1_service.py tests\test_draft_day_app_v1_service.py tests\test_navigation_compression.py` - passed.
- `git diff --check` - passed.

## Master Integration Note

Merge branch `codex/dynasty-outcome-player-board-20260622` from worktree `C:\NWR\Niners-War-Room-dynasty-outcome-player-board`. This lane safely repairs Dynasty Rankings into one player-board experience with full dynasty rows, frozen-board-only rows, and display-only Outcome context. It does not mutate frozen board data, pinned/latest exchange snapshots, model logic, ranks, Outcome probabilities, or simulator behavior. Master should preserve the source fallback to the approved control-repo local dynasty artifact unless a formal shared local dynasty export path is approved later.
