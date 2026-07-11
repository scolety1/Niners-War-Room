# Live / Mock Behavior Equivalence Review

## Live Draft

PASS. The command-center summary still loads the same live runtime state and uses the same cockpit summary service. Its function now returns the already-loaded state so secondary read-only rails can render after the primary workflow. Assignment, undo, remove, draft-board state, table population, current pick/team, drafted visibility, completion, persistence, and event logging still run through the existing shared workflow and services.

The new current-pick/team/status and selected-player/pick text are direct readings of the existing summary and selection values. Missing team data is represented as `Not enough information`; no label claims more than the state guarantees.

## Mock Draft

PASS. The active-session key remains `mock_draft_room_active_session_id`. The workflow key remains `draft_day_v1_mock_draft_workflow_<draft_id>`, and the shared runtime key remains derived from it. Saved-session create, rename, duplicate, and confirmed delete callbacks retain their service calls and arguments; they are visually grouped in a native expander. Reset and persistence boundaries are unchanged.

Mock continues to use `mode="mock"` and the selected mock `draft_id`; Live continues to use the live scope. The 11-case baseline/source differential and expanded runtime tests prove actions do not cross scopes.

## Preserved behavior

- Unified table and draft board: preserved.
- Assignment, undo, remove, and auto-advance: preserved.
- Drafted rows hidden by default and drafted-player toggle: preserved.
- ADP display-only meaning, age display, current-pick value, and ADP range context: preserved.
- Player pool, eligibility, sorting, filtering, rankings, recommendations, and source status: unchanged.
- Free-agent pool wiring: unchanged; no repair or expansion was attempted.
