# NWR Live + Mock Draft Workflow Upgrade - 2026-06-22

## Scope

This upgrade turns the Draft-Day App V1 Live Draft Room and Mock Draft pages into
manual draft workflow surfaces. It does not change the frozen board, ranking logic,
simulator valuation logic, pinned snapshots, `latest_candidate`, or `latest_approved`.

## Source Of Truth

- Frozen board: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- Expected row count: 66
- Pick context: Mock Draft lane app props under `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\mock_draft`

The frozen board remains the ranking source. All sorting in the app is visible and
user-controlled.

## Live Draft Room

The Live Draft Room now uses one main ranking table and a draft board below it.

Operator controls:

- Draft status filter: available only, all, drafted only
- Position filter
- Tier filter
- target/watch/avoid display-only action filter when present
- Manual-review filter
- Visible sort selector
- Player search
- Assign selected player to current or chosen pick slot
- Undo last pick
- Remove/edit an assigned pick slot

State is stored in Streamlit `session_state` only. It does not write back to the
frozen board or any source package.

## Mock Draft

Mock Draft now uses the same manual pick-selection workflow and draft board, while
keeping simulator/model logic unchanged. The page copy explicitly labels the mode as
manual mock practice, not an automated simulator run.

## Draft Board

The draft board displays:

- overall pick
- round/pick label
- owner
- NWR pick marker
- current/open/drafted status
- selected player, position, NFL team
- frozen-board rank and tier when a player is assigned

## Guardrails

Confirmed by design:

- No frozen-board mutation
- No final-board rank changes
- No player additions/removals
- No model/value/ranking logic changes
- No hidden sort fields
- No ADP/market/projection/trade calculator input to value
- No app prop or Lane Exchange promotion changes
- No raw vendor CSV or prediction dump added
- No hosted deployment

## Validation Targets

Focused service tests cover:

- player can be marked picked
- duplicate player assignment is rejected with a user-facing error
- undo restores availability
- draft board state updates
- pick assignment can be removed/edited
- frozen board still loads 66 rows
- display frames do not expose internal/source columns

Browser smoke should confirm:

- Live Draft Room has one main ranking table plus draft board
- player assignment updates draft board
- undo restores state
- Mock Draft has the same manual draft board workflow
- no Streamlit exceptions across all nine V1 pages
