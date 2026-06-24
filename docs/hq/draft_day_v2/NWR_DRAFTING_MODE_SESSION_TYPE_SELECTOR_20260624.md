# NWR Drafting Mode Session Type Selector

Date: 2026-06-24

## What Changed

Drafting Mode now exposes an explicit top-bar `Draft Session:` selector with:

- `Live Draft`
- `Mock Draft / Practice`

The cockpit displays the active badge as `LIVE DRAFT MODE` or `MOCK PRACTICE MODE`.

## Runtime State Behavior

The existing runtime state service already stores state by mode under the ignored local runtime root:

- live state: `draft_day_v2__live.json`
- mock state: `draft_day_v2__mock.json`

Drafting Mode now loads, saves, exports, records trades, records notes, marks drafted players, and resets state through the selected session mode. Existing/default runtime state remains treated as live unless mock mode is explicitly selected.

## Live vs Mock Guardrails

- Mock drafted players do not affect live state.
- Live drafted players do not affect mock state.
- Mock trade events do not affect live pick ownership overrides.
- Live trade events do not affect mock pick ownership overrides.
- Mock mode shows: `Practice state only — does not affect live draft.`
- Live reset requires an explicit confirmation checkbox and warns that live picks and trades will be cleared.
- Mock reset affects only mock/practice state.

## Related Pages

Post-Draft Mode continues to default to `Live` state.

Cheat Sheets still defaults to live state on direct load. When opened from the Drafting Mode deep-tools rail, it receives `session_type=live` or `session_type=mock` and reads the matching cockpit runtime state.

The existing `/mock-draft` page remains available as a deep tool.

## Refresh Data Preservation

The cockpit top bar continues to preserve the `Refresh Data` control when the refresh orchestrator service is present. The navigation placement before `Mock Draft`, `/refresh-data`, and Settings/Data Health refresh-status behavior are unchanged.

## Guardrails

This change does not:

- mutate Frozen Final Draft Board V1.
- change `final_board_rank`.
- overwrite Dynasty Rank.
- change tier assignments.
- update `latest_candidate`, `latest_approved`, or pinned snapshots.
- change model/rank logic.
- make DynastyProcess, ADP, or market context model inputs.
- track runtime JSON, `local_exports`, `C:\NWR_SHARED_DATA`, raw vendor files, or email bodies.

## Tests And Checks

Focused coverage was added for:

- separate live/mock state paths.
- live drafted players staying out of mock state.
- mock drafted players staying out of live state.
- trade events separated by session type.
- export/import preserving selected session type.
- reset affecting only the selected session type.
- Post-Draft Mode defaulting to live.
- Drafting Mode top bar exposing the selector and reset warning.
- Cheat Sheets reading cockpit `session_type` when launched from the cockpit.

## Known Caveats

The selector is cockpit-local. Direct page loads outside Drafting Mode keep conservative defaults: live state for Cheat Sheets and Post-Draft Mode unless a cockpit link provides a session query.
