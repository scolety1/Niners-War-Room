# NWR Live Draft V2 Persistence And Trade Events - 2026-06-23

## Verdict

GREEN. This patch upgrades Draft Mode reliability only. It does
not change model logic, rank logic, tier assignments, source-truth files, latest pointers, or
pinned snapshots.

## Persistence Path

Runtime draft state is local-only and outside tracked repo data:

```text
C:\NWR_SHARED_DATA\draft_runtime_state
```

Subfolders:

- `state`: canonical runtime JSON by draft session and mode.
- `exports`: JSON/CSV/Markdown exports.
- `backups`: automatic and manual JSON backups.

Repo fallback ignore rules also cover accidental local folders named `draft_runtime_state/`
or `draft_day_runtime/`.

## Draft State Schema

Canonical JSON fields:

- `schema_version`: `draft_day_runtime_v2`.
- `draft_session_id`: stable draft session id.
- `draft_id`: compatibility alias for `draft_session_id`.
- `mode`: `live`, `mock`, or another explicit workflow mode.
- `source_checkpoint`: display caption for source context.
- `source_version`: optional source/app commit string.
- `app_version`: local app/runtime version label.
- `created_at`, `updated_at`: ISO timestamps.
- `current_pick`: current pick label/number when available.
- `drafted_players`: display list derived from workflow assignments.
- `drafted_player_ids`: stable player keys/ids derived from workflow assignments.
- `workflow_state.assignments`: compatibility bridge used by draft board and cheat sheets.
- `pick_events`: normalized pick-event log.
- `trade_events`: normalized in-draft trade log.
- `pick_ownership_overrides`: pick-label owner overrides from parsed trade assets.
- `event_log`: all draft actions.
- `notes`: manual notes list.

## Pick Event Schema

Pick events include:

- `event_id`
- `timestamp`
- `pick_number`
- `round`
- `pick_in_round`
- `selecting_team`
- `player_name`
- `player_id`
- `position`
- `source`: `manual`, `imported`, or `restored`
- `notes`

## Trade Event Schema

Trade events include:

- `trade_id`
- `timestamp`
- `team_a`
- `team_b`
- `team_a_sends`
- `team_b_sends`
- `team_a_assets`
- `team_b_assets`
- `affected_picks`
- `notes`
- `source`: `manual`
- `status`: `active` or `voided`

Parsed pick assets support:

- Current draft picks such as `2026 1.04` and `2026 2.03`.
- Future picks such as `2028 1st` and `2028 2nd`.
- Bare current-year pick labels such as `1.04`.
- Free-text assets, marked `REVIEW_NEEDED` when parsing cannot safely classify them.

## What Works

- Picked/drafted players are saved to local JSON after draft actions.
- Live Draft and Mock Draft remain separate runtime modes.
- Reload/load restores workflow assignments.
- Cheat Sheets V2 hides drafted rows by default using persisted live state.
- Manual save and latest-state load controls are available in Live Draft.
- JSON/CSV/Markdown export is available under the runtime exports folder.
- JSON download/import restore is available from the page.
- Manual and automatic backups are written under the runtime backups folder.
- Reset requires explicit confirmation.
- Record Trade supports Team A/Team B, sends fields, notes, parsing, and event logging.
- Parsed current-year pick assets update visible pick ownership where labels match the board.

## What Remains Manual

- Trade asset parsing does not infer ambiguous player names.
- Future picks are logged but cannot update the current 2026 draft board.
- Free-text assets are retained with `REVIEW_NEEDED`.
- Source-system synchronization back to Sleeper or any hosted tool remains out of scope.

## Intentionally Not Model/Rank/Source Truth

This patch does not:

- Mutate Frozen Final Draft Board V1.
- Change `final_board_rank`.
- Overwrite Dynasty Rank.
- Change tier assignments.
- Update `latest_candidate` or `latest_approved`.
- Mutate pinned snapshots.
- Change model/rank logic.
- Promote market, ADP, or DynastyProcess fields into model inputs.
- Create hidden sort drivers from display-only fields.

## Tests And Checks

Focused tests:

```text
python -m pytest tests/test_draft_day_runtime_state_service.py tests/test_draft_day_workflow_service.py tests/test_cheat_sheets_v2_page.py tests/test_draft_day_app_v1_service.py tests/test_dynasty_rankings_page_v1.py
```

Result: `64 passed`.

Touched-file Ruff:

```text
python -m ruff check src/services/draft_day_runtime_state_service.py app/components/draft_workflow.py app/pages/21_live_draft_room_v1.py app/pages/19_drafting_mode_v2.py tests/test_draft_day_runtime_state_service.py
```

Result: passed.

## Browser Smoke

Browser smoke was run against a clean local Streamlit server on `127.0.0.1:8765` with
isolated runtime root `C:\NWR_SHARED_DATA\draft_runtime_state_smoke_v3`.

Routes loaded without app exceptions:

- `/live-draft-room`
- `/cheat-sheets`
- `/drafting-mode`
- `/rankings`
- `/player-compare`
- `/trading-lab`
- `/mock-draft`

Interaction proof:

- Marked `Jeremiyah Love` drafted at `1.01`.
- Page showed `Drafted: 1` and advanced to `Current pick: 1.02`.
- Clicked `Save draft state`.
- Reloaded browser; state still showed `Drafted: 1` and `Current pick: 1.02`.
- Clicked `Load latest draft state`; state still showed `Drafted: 1` and `Current pick: 1.02`.
- Opened `/cheat-sheets`; it showed `Drafted: 1`, `Current pick: 1.02`, `Hide drafted`
  selected, and the drafted player was not visible in the default view.
- Clicked `Export JSON`; browser showed export success and `Download JSON`.
- Recorded trade:
  - Team A: `NWR`
  - Team B: `Team B`
  - Team A sends: `2026 1.04`
  - Team B sends: `2026 2.03, 2028 1st`
- Runtime event log had 5 events and the last event was `trade_recorded`.
- Runtime trade event stored ownership overrides:
  - `1.04 -> Team B`
  - `2.03 -> NWR`
  - `2028 1st` retained as future pick with no current-board update.
- Clicking `Reset draft state` without confirmation showed the confirmation warning and
  preserved `Drafted: 1`.

## Guardrail Confirmations

Final guardrail confirmations:

- No runtime JSON files tracked.
- No `C:\NWR_SHARED_DATA` files tracked.
- Frozen board remains 66 rows.
- Pinned hash unchanged.
- `latest_candidate` and `latest_approved` untouched.
